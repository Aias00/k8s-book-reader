"""Exercise the book's real Kubernetes objects; requires the isolated kind context."""
from pathlib import Path
import hashlib
import json
import socket
import subprocess
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = 'k8s-book'
CONTEXT = 'kind-k8s-book'


def main():
    (ROOT / '.build').mkdir(exist_ok=True)
    commands = (ROOT / '.build/kind-commands.log').open('w')
    checks = []
    observations = {}

    def kube(*args, data=None, check=True, timeout=180):
        argv = ['kubectl', '--context', CONTEXT, '-n', NAMESPACE, *args]
        result = subprocess.run(argv, input=json.dumps(data) if data is not None else None,
                                text=True, capture_output=True, timeout=timeout)
        commands.write('$ ' + ' '.join(argv) + '\n' + result.stdout + result.stderr + '\n')
        commands.flush()
        if check and result.returncode:
            raise RuntimeError(f'{args}: {result.stderr[-3000:]} {result.stdout[-2000:]}')
        return result

    def document(*args):
        return json.loads(kube(*args, '-o', 'json').stdout)

    def apply(resource):
        kube('apply', '-f', '-', data=resource)

    def wait_for(description, predicate, timeout=120):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = predicate()
            if value:
                return value
            time.sleep(1)
        raise AssertionError('Timed out: ' + description)

    def pod(name):
        return document('get', 'pod', name)

    def ready(value):
        return any(condition['type'] == 'Ready' and condition['status'] == 'True'
                   for condition in value.get('status', {}).get('conditions', []))

    def endpoints(service):
        slices = document('get', 'endpointslices', '-l', 'kubernetes.io/service-name=' + service)
        return [endpoint for item in slices['items'] for endpoint in (item.get('endpoints') or [])
                if endpoint.get('conditions', {}).get('ready') is True]

    def rollout():
        kube('rollout', 'status', 'deployment/hello-web', '--timeout=150s')
        wait_for('two ready Service endpoints', lambda: len(endpoints('hello-web')) == 2)

    def get_http(service='hello-web', check=True):
        return kube('exec', 'netcheck', '--', 'wget', '-qO-', '-T', '5', 'http://' + service,
                    check=check, timeout=20)

    try:
        current = subprocess.check_output(['kubectl', 'config', 'current-context'], text=True).strip()
        assert current == CONTEXT, f'Refusing context {current}'
        versions = document('version')
        observations['versions'] = versions
        kube('wait', '--for=condition=Ready', 'nodes', '--all', '--timeout=180s')
        kube('apply', '-f', 'examples/project/namespace.yaml')
        kube('apply', '-f', 'examples/pod.yaml')
        kube('wait', '--for=condition=Ready', 'pod/hello-pod', '--timeout=150s')
        kube('delete', 'pod', 'hello-pod', '--wait=true')
        assert not document('get', 'pods', '-l', 'app=hello-pod')['items']
        kube('apply', '-f', 'examples/deployment-basic.yaml')
        kube('rollout', 'status', 'deployment/hello-web', '--timeout=150s')
        for name in ['configmap.yaml', 'deployment.yaml', 'service.yaml']:
            kube('apply', '-f', 'examples/project/' + name)
        rollout()
        checks.append('all seven source YAML files applied to real API (storage applied later)')

        apply({'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'netcheck'},
               'spec': {'containers': [{'name': 'tools', 'image': 'busybox:1.37',
                                         'command': ['sh', '-c', 'sleep 3600']}]}})
        kube('wait', '--for=condition=Ready', 'pod/netcheck', '--timeout=150s')
        dns = kube('exec', 'netcheck', '--', 'nslookup', 'hello-web.k8s-book.svc.cluster.local').stdout
        assert 'hello-web.k8s-book.svc.cluster.local' in dns
        welcome = get_http().stdout
        assert '你好，Kubernetes！' in welcome
        assert '你好，Kubernetes！' in get_http('hello-web.k8s-book.svc.cluster.local').stdout
        observations['dns'] = dns
        checks.append('Service DNS and actual in-cluster HTTP include ConfigMap Chinese page')

        with socket.socket() as connection:
            connection.bind(('127.0.0.1', 0))
            port = connection.getsockname()[1]
        forward_log = (ROOT / '.build/port-forward.log').open('w')
        forward = subprocess.Popen(['kubectl', '--context', CONTEXT, '-n', NAMESPACE, 'port-forward',
                                    'service/hello-web', f'{port}:80'], stdout=forward_log, stderr=subprocess.STDOUT)
        try:
            def local_page():
                try:
                    with urlopen(f'http://127.0.0.1:{port}', timeout=2) as response:
                        return response.status == 200 and '你好，Kubernetes！' in response.read().decode()
                except OSError:
                    return False
            wait_for('port-forward HTTP', local_page, 30)
        finally:
            forward.terminate()
            forward.wait(timeout=10)
            forward_log.close()
        checks.append('host port-forward actual HTTP (not a load-balancing assertion)')

        initial = document('get', 'pods', '-l', 'app=hello-web')['items']
        old_uid = initial[0]['metadata']['uid']
        kube('delete', 'pod', initial[0]['metadata']['name'], '--wait=true')
        rollout()
        assert old_uid not in {item['metadata']['uid'] for item in document('get', 'pods', '-l', 'app=hello-web')['items']}
        kube('scale', 'deployment/hello-web', '--replicas=3')
        kube('rollout', 'status', 'deployment/hello-web', '--timeout=150s')
        wait_for('three ready endpoints', lambda: len(endpoints('hello-web')) == 3)
        kube('apply', '-f', 'examples/project/deployment.yaml')
        rollout()
        checks.append('Deployment replacement UID, scale to three, declarative restore to two')

        probe = {'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': 'probe-demo', 'labels': {'app': 'probe-demo'}},
                 'spec': {'terminationGracePeriodSeconds': 1, 'containers': [{'name': 'web', 'image': 'nginx:1.28',
                    'command': ['sh', '-c', "echo ready > /usr/share/nginx/html/ready.html; echo live > /usr/share/nginx/html/live.html; exec nginx -g 'daemon off;'"],
                    'readinessProbe': {'httpGet': {'path': '/ready.html', 'port': 80}, 'periodSeconds': 2, 'failureThreshold': 1},
                    'livenessProbe': {'httpGet': {'path': '/live.html', 'port': 80}, 'periodSeconds': 2,
                                      'failureThreshold': 1, 'terminationGracePeriodSeconds': 1}}]}}
        apply(probe)
        apply({'apiVersion': 'v1', 'kind': 'Service', 'metadata': {'name': 'probe-demo'},
               'spec': {'selector': {'app': 'probe-demo'}, 'ports': [{'port': 80, 'targetPort': 80}]}})
        kube('wait', '--for=condition=Ready', 'pod/probe-demo', '--timeout=150s')
        wait_for('ready probe endpoint', lambda: len(endpoints('probe-demo')) == 1)
        original_restarts = pod('probe-demo')['status']['containerStatuses'][0]['restartCount']
        kube('exec', 'probe-demo', '--', 'rm', '/usr/share/nginx/html/ready.html')
        wait_for('readiness failure removes endpoint', lambda: not ready(pod('probe-demo')) and not endpoints('probe-demo'))
        time.sleep(5)
        assert pod('probe-demo')['status']['containerStatuses'][0]['restartCount'] == original_restarts
        kube('exec', 'probe-demo', '--', 'touch', '/usr/share/nginx/html/ready.html')
        kube('wait', '--for=condition=Ready', 'pod/probe-demo', '--timeout=90s')
        kube('exec', 'probe-demo', '--', 'rm', '/usr/share/nginx/html/live.html')
        wait_for('liveness restarts container', lambda: pod('probe-demo')['status']['containerStatuses'][0]['restartCount'] > original_restarts, 120)
        kube('wait', '--for=condition=Ready', 'pod/probe-demo', '--timeout=90s')
        checks.append('HTTP readiness failure removes endpoint without restart; HTTP liveness failure increases restartCount')

        kube('set', 'image', 'deployment/hello-web', 'web=nginx:this-tag-does-not-exist-k8s-book')
        failed = kube('rollout', 'status', 'deployment/hello-web', '--timeout=30s', check=False, timeout=45)
        assert failed.returncode != 0
        def image_failure():
            items = document('get', 'pods', '-l', 'app=hello-web')['items']
            return [state['state']['waiting']['reason'] for item in items
                    for state in item.get('status', {}).get('containerStatuses', [])
                    if state.get('state', {}).get('waiting', {}).get('reason') in {'ErrImagePull', 'ImagePullBackOff'}]
        observations['bad_image_reasons'] = wait_for('bad image pull failure', image_failure, 90)
        assert len(endpoints('hello-web')) >= 2 and '你好，Kubernetes！' in get_http().stdout
        kube('rollout', 'undo', 'deployment/hello-web')
        rollout()
        assert document('get', 'deployment', 'hello-web')['spec']['template']['spec']['containers'][0]['image'] == 'nginx:1.28'
        checks.append('bad image rollout fails while old endpoints serve; rollback restores original image and two ready endpoints')

        kube('patch', 'configmap', 'hello-page', '--type=merge', '-p',
             json.dumps({'data': {'index.html': '<h1>我完成了第一次配置更新</h1>'}}, ensure_ascii=False))
        kube('rollout', 'restart', 'deployment/hello-web')
        rollout()
        assert '我完成了第一次配置更新' in get_http().stdout
        checks.append('ConfigMap change plus explicit rolling restart updates real HTTP content')
        kube('patch', 'service', 'hello-web', '--type=merge', '-p', json.dumps({'spec': {'selector': {'app': 'wrong-app'}}}))
        wait_for('wrong selector removes endpoints', lambda: not endpoints('hello-web'))
        wait_for('wrong selector breaks real HTTP', lambda: get_http(check=False).returncode != 0, 30)
        kube('apply', '-f', 'examples/project/service.yaml')
        wait_for('restored selector has endpoints', lambda: len(endpoints('hello-web')) == 2)
        assert '我完成了第一次配置更新' in get_http().stdout
        checks.append('wrong Service selector breaks actual HTTP; restoring selector recovers traffic')

        kube('apply', '-f', 'examples/storage.yaml')
        kube('wait', '--for=condition=Ready', 'pod/notes-writer', '--timeout=180s')
        pvc_before = document('get', 'pvc', 'notes')
        writer_before = pod('notes-writer')['metadata']['uid']
        kube('exec', 'notes-writer', '--', 'sh', '-c', 'echo hello-storage-ci > /data/note.txt')
        kube('delete', 'pod', 'notes-writer', '--wait=true')
        kube('apply', '-f', 'examples/storage.yaml')
        kube('wait', '--for=condition=Ready', 'pod/notes-writer', '--timeout=180s')
        assert pod('notes-writer')['metadata']['uid'] != writer_before
        assert document('get', 'pvc', 'notes')['metadata']['uid'] == pvc_before['metadata']['uid']
        assert kube('exec', 'notes-writer', '--', 'cat', '/data/note.txt').stdout.strip() == 'hello-storage-ci'
        observations['storage_class'] = pvc_before['spec']['storageClassName']
        checks.append('PVC identity and file survive Pod replacement on the same kind node (not node-loss recovery)')

        for name, extra in [('cpu-too-large', {'containers': [{'name': 'tools', 'image': 'busybox:1.37',
                    'command': ['sleep', '3600'], 'resources': {'requests': {'cpu': '1000000', 'memory': '64Mi'}}}]}),
                  ('selector-mismatch', {'nodeSelector': {'book.example/absent': 'yes'},
                    'containers': [{'name': 'tools', 'image': 'busybox:1.37', 'command': ['sleep', '3600']}]})]:
            apply({'apiVersion': 'v1', 'kind': 'Pod', 'metadata': {'name': name}, 'spec': extra})
            def unschedulable():
                return [item for item in pod(name)['status'].get('conditions', [])
                        if item['type'] == 'PodScheduled' and item['status'] == 'False' and item.get('reason') == 'Unschedulable']
            condition = wait_for(name + ' rejected by scheduler', unschedulable)[0]
            assert pod(name)['status']['phase'] == 'Pending'
            observations[name] = condition['message']
        assert 'Insufficient cpu' in observations['cpu-too-large']
        checks.append('oversized CPU request and unmatched node selector stay Pending with actual Unschedulable evidence')
        observations['container_images'] = [{state['image']: state.get('imageID')}
            for item in document('get', 'pods')['items'] for state in item.get('status', {}).get('containerStatuses', [])]
        report = dict(date='2026-10-21', result='PASS', checks=checks, observations=observations,
                      manifest_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in sorted((ROOT / 'examples').rglob('*.yaml'))},
                      test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      untested=['multi-node failover', 'node/cluster deletion storage recovery', 'production TLS/RBAC security baseline',
                                'HPA and Metrics Server', 'NetworkPolicy enforcement', 'OOM/CPU throttling load experiment', 'production load'])
        (ROOT / 'research/runtime-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'result': 'PASS', 'checks': checks}, ensure_ascii=False))
    except Exception as error:
        (ROOT / 'research/runtime-validation.json').write_text(json.dumps({'result': 'FAIL', 'completed_checks': checks,
            'error': str(error)}, ensure_ascii=False, indent=2) + '\n')
        raise
    finally:
        commands.close()


if __name__ == '__main__':
    main()
