from kubernetes import client, config
import json
import inquirer

def get_context():
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Cannot find any context in kube-config file.")
        return

    contexts = [context['name'] for context in contexts]

    return inquirer.prompt([inquirer.List('context',
                  message="Which context should I pick?",
                  choices=contexts,
              )
    ])

def get_namespace(metadata):
    metadata['namespace'] = ''
    v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=metadata['context']))
    namespace = v1.list_namespace(watch=False)
    namespaces = [ns.metadata.name for ns in namespace.items]
    metadata['namespace'] = inquirer.prompt([inquirer.List('namespace',
                  message="Which namespace should I pick?",
                  choices=namespaces,
                )
        ])['namespace']
    return metadata

def get_pod(metadata):
    metadata['pod'] = ''
    v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=metadata['context']))
    pod = v1.list_namespaced_pod(metadata['namespace'], watch=False)
    pods = [po.metadata.name for po in pod.items]
    metadata['pod'] = inquirer.prompt([inquirer.List('pod',
                  message="Which pod should I pick?",
                  choices=pods,
                )
        ])['pod']

    return pod.items[pods.index(metadata['pod'])].spec.containers[0].env

def main():
    print("Select pod for first candidate.")
    a = [env.name for env in get_pod(get_namespace(get_context()))]
    print("--------------------------------")
    print("Select pod for second candidate.")
    b = [env.name for env in get_pod(get_namespace(get_context()))]
    print("--------------------------------")
    print(list(set(a) - set(b)))

main()
