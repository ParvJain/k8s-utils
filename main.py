from kubernetes import client, config
import json
import inquirer
from terminaltables import AsciiTable
from blessings import Terminal

term = Terminal()

def get_context():
    contexts, active_context = config.list_kube_config_contexts()
    if not contexts:
        print("Cannot find any context in kube-config file.")
        return

    contexts = [context['name'] for context in contexts]

    return inquirer.prompt([inquirer.List('context',
                  message="Which context you want to pick?",
                  choices=contexts,
              )
    ])

def get_namespace(metadata):
    metadata['namespace'] = ''
    v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=metadata['context']))
    namespace = v1.list_namespace(watch=False)
    namespaces = [ns.metadata.name for ns in namespace.items]
    metadata['namespace'] = inquirer.prompt([inquirer.List('namespace',
                  message="Which namespace you want to pick?",
                  choices=namespaces,
                )
        ])['namespace']
    return metadata

def get_pod(metadata):
    metadata['pod'] = []
    metadata['pod_name'] = ''
    v1 = client.CoreV1Api(api_client=config.new_client_from_config(context=metadata['context']))
    pod = v1.list_namespaced_pod(metadata['namespace'], watch=False)
    pods = [po.metadata.name for po in pod.items]
    metadata['pod_name'] = inquirer.prompt([inquirer.List('pod',
                  message="Which pod you want to pick?",
                  choices=pods,
                )
        ])['pod']
    metadata['pod'] = pod.items[pods.index(metadata['pod_name'])].spec.containers[0].env
    return metadata

def main():
    print("Select pod for first candidate.")
    a = get_pod(get_namespace(get_context()))
    a_env = {env.name:env.value for env in a['pod']}
    print("--------------------------------")
    print("Select pod for second candidate.")
    b = get_pod(get_namespace(get_context()))
    b_env = {env.name:env.value for env in b['pod']}
    datapoints = [
        ["Data points", "Values"],
        [f"Environment variable in {a['context']} » {a['namespace']} » {a['pod_name']}", str(len(a_env.items()))],
        [f"Environment variable in {b['context']} » {b['namespace']} » {b['pod_name']}", str(len(b_env.items()))],
        [f"Conflicting environment key(s) count in {a['pod_name']}", str(len(list(a_env.keys() - b_env.keys())))],
        [f"Missing keys in {a['pod_name']}", str(list(a_env.keys() - b_env.keys()))],
        [f"Conflicting environment key(s) count in {b['pod_name']}", str(len(list(b_env.keys() - a_env.keys())))],
        [f"Missing keys in {b['pod_name']}", str(list(b_env.keys() - a_env.keys()))]
    ]
    print(AsciiTable(datapoints).table)

    compare_var_table = []
    compare_var_table.append(['Key', f"{a['pod_name'].strip()}", f"{b['pod_name'].strip()}"])
    for key in set(list(a_env.keys()) + list(b_env.keys())):
        a_val = a_env[key] if key in a_env else '❗❗<MISSING>❗❗'
        b_val = b_env[key] if key in b_env else '❗❗<MISSING>❗❗'
        c_key = key
        if ((key not in a_env) or (key not in b_env)):
            c_key = term.red + key + term.normal
        elif a_val != b_val:
            c_key = term.yellow + key + term.normal
        else:
            c_key = term.green + key + term.normal
        compare_var_table.append([c_key, a_val, b_val])
    
    print(AsciiTable(compare_var_table).table)

if __name__ == "__main__": 
    main()
