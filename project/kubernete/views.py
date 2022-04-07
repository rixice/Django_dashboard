import re
import smtplib, os, datetime, paramiko
import threading
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep

import chardet
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from .models import pods, services, users, name_spaces, nodes, deploys, backup_log, log_file, hosts
from kubernetes import client, config

mysql_passwd = 'MYSQL_PASSWD'
localhost = 'LOCALHOST'


########################## 登录与注册 ####################################################

def register(request):
    host_ip = request.COOKIES.get('host_ip')
    if request.method == 'GET':
        usr_name = request.COOKIES.get('usr_name')
        if not usr_name:
            return HttpResponseRedirect('/login')
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'register.html', locals())
        ERROR = '当前用户不具备管理权限'
        return render(request, 'management.html', locals())
    elif request.method == 'POST':
        usr_name = request.POST['usr_name']
        check = users.objects.filter(name=usr_name).exists()
        if check:
            return HttpResponse("该用户已存在！")
        else:
            usr_passwd = request.POST['usr_passwd']
            users.objects.create(name=usr_name, password=usr_passwd)
            host_name = os.popen("hostname").read()
            host_name = run(host_ip, "root", "hostname").decode("utf-8")
            system_info = run(host_ip, "root", "cat /proc/version").decode('utf-8')
            cpu_info = run(host_ip, "root", "cat /proc/cpuinfo| grep 'model name'| uniq| cut -d ' ' -f3-").decode(
                'utf-8')
            disk_total = run(host_ip, "root", "fdisk -l |grep G | awk 'NR==1{print$3$4}'| cut -d ',' -f1").decode(
                'utf-8')
            disk_used = run(host_ip, "root", "df -h| grep /dev/sd| grep G| awk '{print$5}'").decode('utf-8')
            reg = render(request, 'index_1.html', locals())
            reg.set_cookie('usr_name', usr_name)
            return reg


def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        usr_name = request.POST['usr_name']
        usr_passwd = request.POST['usr_passwd']
        for i in users.objects.filter(is_active=True):
            if usr_name == i.name and usr_passwd == i.password:
                root_usr = users.objects.filter(is_root=True)
                usr_access = '✘'
                for n in root_usr:
                    if usr_name == n.name:
                        usr_access = '✔'
                host_ip = os.popen("bash /root/shell/mechine_ip.sh").read()
                host_name = run(host_ip, "root", "hostname").decode("utf-8")
                system_info = run(host_ip, "root", "cat /proc/version").decode('utf-8')
                cpu_info = run(host_ip, "root", "cat /proc/cpuinfo| grep 'model name'| uniq| cut -d ' ' -f3-").decode(
                    'utf-8')
                disk_total = run(host_ip, "root", "fdisk -l |grep G | awk 'NR==1{print$3$4}'| cut -d ',' -f1").decode(
                    'utf-8')
                disk_used = run(host_ip, "root", "df -h| grep /dev/sd| grep G| awk '{print$5}'").decode('utf-8')
                ans = render(request, 'index_1.html', locals())
                ans.set_cookie('usr_name', usr_name)
                ans.set_cookie('host_ip', host_ip)
                return ans
        ERROR = "用户名或密码错误，请重试"
        return render(request, 'login.html', locals())


############################# Management用户与主机管理 ################################################

def management(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    ###############################################
    for n in root_usr:
        if usr_name == n.name:
            all_usr = users.objects.all()
            all_host = hosts.objects.all()

            for i in all_usr:
                if i.is_active:
                    i.is_active = '✔'
                else:
                    i.is_active = '✘'
                if i.is_root:
                    i.is_root = '✔'
                else:
                    i.is_root = '✘'

            if request.method == 'POST':
                ip = request.POST.get('ip')
                n = int(os.popen("ping -c1 {} |grep '1 received' |wc -l &".format(ip)).read())
                if n == 0:
                    host_status = '✘'
                elif n == 1:
                    host_status = '✔'
                return JsonResponse({"host": ip, "status": host_status})

            TIPS = '注意：如果想让用户无法登录，修改活跃状态即可'
            return render(request, 'management.html', locals())
    ERROR = '当前用户不具备管理权限'
    all_usr = users.objects.filter(name=usr_name)
    return render(request, 'management.html', locals())


def manage_user(request, user_id):
    usr_name = request.COOKIES.get('usr_name')
    root_usr = users.objects.filter(is_root=True)
    if not usr_name:
        return HttpResponseRedirect('/login')
    user_info = users.objects.get(id=user_id)
    if request.method == 'GET':
        for i in root_usr:
            if usr_name == i.name:
                return render(request, 'manage_user.html', locals())
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        usr_active = request.POST['is_active']
        usr_root = request.POST['is_root']
        user_info.is_active = usr_active
        user_info.is_root = usr_root
        user_info.save()
        return HttpResponseRedirect('/management')


def delete_user(request):
    usr_name = request.COOKIES.get('usr_name')
    user_id = request.GET.get('user_id')
    root_usr = users.objects.filter(is_root=True)
    if not usr_name:
        return HttpResponseRedirect('/login')
    user_sel = users.objects.get(id=user_id)
    if request.method == 'GET':
        for i in root_usr:
            if usr_name == i.name:
                user_sel.delete()
        return HttpResponseRedirect('/management')


###################### 添加远程监控主机 ###################################
def create_host(request):
    if request.method == 'GET':
        return render(request, "create_host.html")
    elif request.method == 'POST':
        host_ip = request.POST['host_ip']
        host_name = request.POST['host_name']
        host_passwd = request.POST['host_passwd']
        n = int(os.popen("ping -c1 {} |grep '1 received' |wc -l &".format(host_ip)).read())
        if n == 1:
            os.system("bash /root/shell/ssh_ip.sh {} {}".format(host_ip, host_passwd))
            os.system("bash /root/shell/ssh_check.sh {}".format(host_ip))
            hosts.objects.create(host_ip=host_ip, host_name=host_name)
            all_hosts = hosts.objects.all()
            return HttpResponseRedirect('/management')
        else:
            ERROR = 'IP或密码有误，请重新确认！'
            return render(request, 'create_host.html', locals())


def delete_host(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.GET.get('host_ip')
    root_usr = users.objects.filter(is_root=True)
    if not usr_name:
        return HttpResponseRedirect('/login')
    host_sel = hosts.objects.get(host_ip=host_ip)
    if request.method == 'GET':
        for i in root_usr:
            if usr_name == i.name:
                host_sel.delete()
        return HttpResponseRedirect('/management')


def change_host(request, host_ip):
    ans = HttpResponseRedirect('/management')
    ans.set_cookie('host_ip', host_ip)
    return ans


###################### 系统监控与管理 ###################################

def monitor(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    ############################ 实时监控 #####################################
    cpu_used = float(run(host_ip, "root", "bash /root/shell/cpu_used.sh &"))
    mem_used = run(host_ip, "root", "bash /root/shell/mem_free2.sh &").decode('utf-8')
    mem_total = run(host_ip, "root", "top -b -n1| awk 'NR==4{print$4}' &").decode('utf-8')
    mem_used_percent = (int(mem_used) / int(mem_total) * 100).__round__(1)
    process_top = run(host_ip, "root", "bash /root/shell/process.sh &").decode('utf-8')
    top_cpu = run(host_ip, "root", "bash /root/shell/process_cpu.sh &").decode('utf-8')
    ############################## 系统信息 ###################################
    host_name = run(host_ip, "root", "hostname &").decode("utf-8")
    system_info = run(host_ip, "root", "cat /proc/version &").decode('utf-8')
    cpu_info = run(host_ip, "root", "cat /proc/cpuinfo| grep 'model name'| uniq| cut -d ' ' -f3- &").decode('utf-8')
    disk_total = run(host_ip, "root", "fdisk -l |grep G | awk 'NR==1{print$3$4}'| cut -d ',' -f1 &").decode('utf-8')
    disk_used = run(host_ip, "root", "df -h| grep /dev/sd| grep G| awk '{print$5}' &").decode('utf-8')
    #################################################################
    # if mem_used_percent > 80:
    #     free_mem()
    if request.method == 'POST':
        num1 = cpu_used
        num2 = mem_used_percent
        num3 = process_top
        num4 = top_cpu
        return JsonResponse({"datas": {"num1": num1, "num2": num2, "num3": num3, "num4": num4}})
    return render(request, 'index_1.html', locals())


def console(request):
    host_ip = request.COOKIES.get('host_ip')
    usr_name = request.COOKIES.get('usr_name')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    host = localhost
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    return render(request, 'console.html', locals())


def free_mem(request):
    host_ip = request.COOKIES.get('host_ip')
    run(host_ip, "root", "echo 3 > /proc/sys/vm/drop_caches")
    return HttpResponseRedirect("/monitor")


def send_mail(host_ip):
    # 第三方SMTP服务
    mail_host = 'smtp.qq.com'
    mail_user = '1330740671'
    mail_pass = 'brzjshccttmmhcdi'
    sender = '1330740671@qq.com'
    receivers = ['1330740671@qq.com']

    run(host_ip, "root", "top -b -n1>/var/log/top_info.log")  # 记录这一时刻的系统使用情况

    message = MIMEMultipart('related')
    message_content = '服务器内存过高警告！！！'
    message['Subject'] = Header(message_content, 'utf-8')

    body_content = '内存使用率过高！！！请及时查看！'
    message_text = MIMEText(body_content, 'plain', 'utf-8')
    message.attach(message_text)

    file = f"/var/log/top_info.log"
    log = MIMEText(open(file, 'r').read(), "base64", "utf-8")
    log['Content-Disposition'] = 'attachment;filename="log.txt"'
    message.attach(log)

    try:
        server = smtplib.SMTP_SSL(mail_host, 465)
        server.login(mail_user, mail_pass)
        server.sendmail(sender, receivers, message.as_string())
        server.quit()
    except smtplib.SMTPException as e:
        print(e)


########################## Kubernetes管理 ###############################################

def kuber(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    os.system("kubectl get nodes")
    if int(run(host_ip, "root", "bash /root/shell/check_k8s.sh")) != 0:
        ERROR = "请检查Kubernetes的配置，该节点无响应"
        return render(request, 'kuber_error.html', locals())
    config.kube_config.load_kube_config(config_file='/root/yaml/kubeconfig.yaml')
    v1 = client.CoreV1Api()
    ###########################################
    all_namespaces = name_spaces.objects.all()
    all_services = services.objects.all()
    all_nodes = nodes.objects.all()
    ###########################################
    for all_ns in v1.list_namespace().items:  # 获取namespaces
        try:
            name_spaces.objects.get(namespace=all_ns.metadata.name)
        except Exception as e:
            name_spaces.objects.create(namespace=all_ns.metadata.name)

    nodes.objects.all().delete()  # 获取实时节点状态
    for all_node in v1.list_node().items:
        nodes.objects.create(name=all_node.metadata.name, status=all_node.status.conditions[3].status)

    for all_service in v1.list_service_for_all_namespaces(watch=False).items:  # 获取各服务的信息
        try:
            service_sel = services.objects.get(service_name=all_service.metadata.name)
            if all_service.spec.ports[0].node_port is not None:
                service_sel.out_port = all_service.spec.ports[0].node_port
                service_sel.save()
        except Exception as e:
            if all_service.kind is None:
                if all_service.spec.ports[0].node_port is None:
                    services.objects.create(service_name=all_service.metadata.name,
                                            spec_cluster_ip=all_service.spec.cluster_ip,
                                            namespace=all_service.metadata.namespace)
                else:
                    services.objects.create(service_name=all_service.metadata.name,
                                            spec_cluster_ip=all_service.spec.cluster_ip,
                                            namespace=all_service.metadata.namespace,
                                            out_port=all_service.spec.ports[0].node_port)
            else:
                if all_service.spec.ports[0].node_port is None:
                    services.objects.create(service_name=all_service.metadata.name,
                                            spec_cluster_ip=all_service.spec.cluster_ip,
                                            namespace=all_service.metadata.namespace,
                                            kind=all_service.kind)
                else:
                    services.objects.create(service_name=all_service.metadata.name,
                                            spec_cluster_ip=all_service.spec.cluster_ip,
                                            namespace=all_service.metadata.namespace,
                                            kind=all_service.kind,
                                            out_port=all_service.spec.ports[0].node_port)
    return render(request, 'kuber.html', locals())


def manage_namespace(request, ns_id):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    usr_access = '✘'
    try:
        config.kube_config.load_kube_config(config_file='/root/yaml/kubeconfig.yaml')
        v1 = client.CoreV1Api()
    except Exception as e:
        ERROR = "请检查Kubernetes的配置，该节点无响应"
        return render(request, 'kuber_error.html', locals())
    ##########################################
    ns_info = name_spaces.objects.get(id=ns_id)
    all_pods = pods.objects.all()
    all_pods.delete()
    for pod in v1.list_pod_for_all_namespaces(watch=False).items:
        if pod.status.pod_ip is None:
            pods.objects.create(pod_name=pod.metadata.name,
                                status=pod.status.phase,
                                namespace=pod.metadata.namespace)
        else:
            pods.objects.create(pod_name=pod.metadata.name,
                                pod_ip=pod.status.pod_ip,
                                status=pod.status.phase,
                                namespace=pod.metadata.namespace)

    deploy_num = int(run(host_ip, "root", "bash /root/shell/deploy_num.sh {}".format(ns_info.namespace)))
    for i in range(1, deploy_num + 1):
        dp_name = run(host_ip, "root",
                      "bash /root/shell/get_deploy.sh {}| cut -d '\n' -f{}".format(ns_info.namespace, i)) \
            .decode('utf-8')
        dp_status = run(host_ip, "root",
                        "bash /root/shell/deploy_status.sh {}| cut -d '\n' -f{}".format(ns_info.namespace, i)) \
            .decode('utf-8')
        dp_age = run(host_ip, "root",
                     "bash /root/shell/deploy_age.sh {}| cut -d '\n' -f{}".format(ns_info.namespace, i)) \
            .decode('utf-8')
        try:
            dp = deploys.objects.get(namespace=ns_info.namespace, name=dp_name)
            dp.status = dp_status
            dp.age = dp_age
        except Exception as e:
            deploys.objects.create(namespace=ns_info.namespace,
                                   name=dp_name,
                                   age=dp_age,
                                   status=dp_status)
    if request.method == 'GET':
        sel_pods = pods.objects.filter(namespace=ns_info.namespace)
        sel_deploys = deploys.objects.filter(namespace=ns_info.namespace)
        return render(request, 'manage_namespace.html', locals())


def create_ns(request):
    host_ip = request.COOKIES.get('host_ip')
    if request.method == 'GET':
        usr_name = request.COOKIES.get('usr_name')
        if not usr_name:
            return HttpResponseRedirect('/login')
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'create_ns.html', locals())
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        name = request.POST['ns_name']
        req_choice = request.POST['req_choice']
        sel_ns = name_spaces.objects.filter(namespace=name)
        if sel_ns.exists():
            ERROR = '该命名空间已存在'
            return render(request, 'create_ns.html', locals())
        else:
            if req_choice != 'True':
                run(host_ip, "root", "kubectl create namespace {}".format(name))
                name_spaces.objects.create(namespace=name)
            elif req_choice == 'True':
                pod_cpu_max = request.POST['pod_cpu_max']
                pod_mem_max = request.POST['pod_mem_max']
                pod_cpu_min = request.POST['pod_cpu_min']
                pod_mem_min = request.POST['pod_mem_min']
                ctn_cpu_def = request.POST['ctn_cpu_def']
                ctn_mem_def = request.POST['ctn_mem_def']
                ctn_cpu_req = request.POST['ctn_cpu_req']
                ctn_mem_req = request.POST['ctn_mem_req']
                ctn_cpu_max = request.POST['ctn_cpu_max']
                ctn_mem_max = request.POST['ctn_mem_max']
                ctn_cpu_min = request.POST['ctn_cpu_min']
                ctn_mem_min = request.POST['ctn_mem_min']
                run(host_ip, "root",
                    "echo 'apiVersion: v1\nkind: LimitRange\nmetadata:\n  name: mylimits\n"
                    "spec:\n  limits:\n  - max:\n      cpu: {}\n      memory: {}\n"
                    "    min:\n      cpu: {}\n      memory: {}\n    type: Pod\n\n"
                    "  - default:\n      cpu: {}\n      memory: {}\n    defaultRequest:\n"
                    "      cpu: {}\n      memory: {}\n    max:\n      cpu: {}\n      memory: {}\n"
                    "    min:\n      cpu: {}\n      memory: {}\n    type: Container"
                    "'>/root/yaml/limits.yaml".format(pod_cpu_max, pod_mem_max,
                                                      pod_cpu_min, pod_mem_min,
                                                      ctn_cpu_def, ctn_mem_def,
                                                      ctn_cpu_req, ctn_mem_req,
                                                      ctn_cpu_max, ctn_mem_max,
                                                      ctn_cpu_min, ctn_mem_min))
                run(host_ip, "root", "kubectl create namespace {}".format(name))
                run(host_ip, "root", "kubectl create -f /root/yaml/limits.yaml -n {}".format(name))
                name_spaces.objects.create(namespace=name)
        return HttpResponseRedirect('/kuber')


def check_service(request, ser_id):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    service = services.objects.get(id=ser_id)
    service_ns = service.namespace
    info = run(host_ip, "root", "kubectl describe service {} -n {}".format(service.service_name, service_ns)).decode(
        'utf-8')
    return render(request, 'check_ser.html', locals())


def create_pd(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'create_pd.html', locals())
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        pod_name = request.POST['pod_name']
        pod_label = request.POST['pod_label']
        ctn_name = request.POST['container_name']
        img_name = request.POST['img_name']
        update_ck = request.POST['update_ck']
        health_ck = request.POST['health_ck']
        ns_nm = request.POST['ns_nm']
        request_ck = request.POST['request_ck']
        if request_ck == 'True':
            port_num = request.POST['port_num']
            run(host_ip, "root",
                "echo 'apiVersion: v1\nkind: Pod\nmetadata:\n  namespace: {}\n  name: {}\n  labels:\n    app: {}\nspec:\n"
                "  containers:\n  - name: {}\n    image: {}\n    ports:\n      - containerPort: {}\n    imagePullPolicy: {}\n  restartPolicy: {}'"
                ">/root/yaml/create-pod.yaml"
                .format(ns_nm, pod_name, pod_label, ctn_name, img_name, port_num, update_ck, health_ck))
        else:
            run(host_ip, "root",
                "echo 'apiVersion: v1\nkind: Pod\nmetadata:\n  namespace: {}\n  name: {}\n  labels:\n    app: {}\nspec:\n"
                "  containers:\n  - name: {}\n    image: {}\n    imagePullPolicy: {}\n  restartPolicy: {}'"
                ">/root/yaml/create-pod.yaml"
                .format(ns_nm, pod_name, pod_label, ctn_name, img_name, update_ck, health_ck))
        run(host_ip, "root", "kubectl apply -f /root/yaml/create-pod.yaml")
        pods.objects.create(pod_name=pod_name, namespace=ns_nm)
        return HttpResponseRedirect('/kuber')


def delete_pd(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'delete_pd.html', locals())
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        pod_name = request.POST['pd_name']
        pod_ns = request.POST['ns_name']
        run(host_ip, "root", "kubectl delete pods {} -n {}".format(pod_name, pod_ns))
        sel = pods.objects.get(pod_name=pod_name, namespace=pod_ns)
        sel.delete()
    return HttpResponseRedirect('/kuber')


def create_dp(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'create_dp.html', locals())
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        api_version = request.POST['api_version']
        pod_name = request.POST['pod_name']
        pod_label = request.POST['pod_label']
        ns_nm = request.POST['ns_nm']
        replicas = int(request.POST['replicas'])
        ctn_1 = request.POST['container_1']
        img_1 = request.POST['img_1']
        port_1 = request.POST['port_1']
        if replicas == 1:
            run(host_ip, "root",
                "echo 'apiVersion: {}\nkind: Deployment\nmetadata:\n  name: {}\n  namespace: {}\nspec:\n"
                "  replicas: {}\n  template:\n    metadata:\n      labels:\n        app: {}\n"
                "    spec:\n      containers:\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n'"
                ">/root/yaml/create-deploy.yaml"
                .format(api_version, pod_name, ns_nm, replicas, pod_label, ctn_1, img_1, port_1))
        if replicas == 2:
            ctn_2 = request.POST['container_2']
            img_2 = request.POST['img_2']
            port_2 = request.POST['port_2']
            run(host_ip, "root",
                "echo 'apiVersion: {}\nkind: Deployment\nmetadata:\n  name: {}\n  namespace: {}\nspec:\n"
                "  replicas: {}\n  template:\n    metadata:\n      labels:\n        app: {}\n"
                "    spec:\n      containers:\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n'"
                ">/root/yaml/create-deploy.yaml"
                .format(api_version, pod_name, ns_nm, replicas, pod_label, ctn_1, img_1, port_1, ctn_2, img_2
                        , port_2))
        if replicas == 3:
            ctn_2 = request.POST['container_2']
            img_2 = request.POST['img_2']
            port_2 = request.POST['port_2']
            ctn_3 = request.POST['container_3']
            img_3 = request.POST['img_3']
            port_3 = request.POST['port_3']
            run(host_ip, "root",
                "echo 'apiVersion: {}\nkind: Deployment\nmetadata:\n  name: {}\n  namespace: {}\nspec:\n"
                "  replicas: {}\n  template:\n    metadata:\n      labels:\n        app: {}\n"
                "    spec:\n      containers:\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n        - name: {}\n          image: {}\n          ports:\n"
                "            - containerPort: {}\n'"
                ">/root/yaml/create-deploy.yaml"
                .format(api_version, pod_name, ns_nm, replicas, pod_label, ctn_1, img_1, port_1, ctn_2, img_2
                        , port_2, ctn_3, img_3, port_3))
        run(host_ip, "root", "kubectl create -f /root/yaml/create-deploy.yaml")
        return HttpResponseRedirect('/kuber')


def delete_dp(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    if request.method == 'GET':
        root_usr = users.objects.filter(is_root=True)
        for n in root_usr:
            if usr_name == n.name:
                return render(request, 'delete_dp.html', locals())
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    elif request.method == 'POST':
        dp_name = request.POST['dp_name']
        dp_id = request.POST['dp_id']
        ns_nm = request.POST['ns_name']
        deploys.objects.get(id=dp_id).delete()
        run(host_ip, "root", "kubectl delete deployment {} -n {}".format(dp_name, ns_nm))
    return HttpResponseRedirect('/kuber')


def pod_info(request, pod_name):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    sel_pod = pods.objects.get(pod_name=pod_name)
    sel_ns = sel_pod.namespace
    info = run(host_ip, "root", "kubectl describe pods {} -n {}".format(pod_name, sel_ns)).decode('utf-8')
    return render(request, 'pod_info.html', locals())


def deploy_info(request, deploy_id):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    sel_dp = deploys.objects.get(id=deploy_id)
    info = run(host_ip, "root", "kubectl describe deploy {} -n {}".format(sel_dp.name, sel_dp.namespace)).decode(
        'utf-8')
    return render(request, 'dp_info.html', locals())


def node_info(request, node_name):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    info = run(host_ip, "root", "kubectl describe node {}".format(node_name)).decode('utf-8')
    return render(request, 'node_Info.html', locals())


############################# Log日志管理 ##############################################
def log(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    ##########################################
    path = "/var/log"
    threading.Thread(target=search_log(path, host_ip)).start()
    # all_log = search_log(path, host_ip)
    all_log = log_file.objects.filter(path_2=path)
    return render(request, 'log.html', locals())


def log_2(request, name):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    #########################################
    if request.method == 'GET':
        path = run(host_ip, "root", "echo -n `find /var/log -name {}`".format(name)).decode('utf-8')  # 确保没有换行符
        path_num = int(run(host_ip, "root", "echo -n `find /var/log -name {}| wc -l`".format(name)))
        if path_num > 1:
            ERROR = "检索到多个同名文件，请手动输入路径"
            return render(request, 'log_2.html', locals())
        # search_log(path, host_ip)
        threading.Thread(target=search_log(path, host_ip)).start()
        # all_log = search_log(path, host_ip)
        all_log = log_file.objects.filter(path_2=path)
        return render(request, 'log_2.html', locals())
    elif request.method == 'POST':
        path = request.POST['path']
        # search_log(path, host_ip)
        threading.Thread(target=search_log(path, host_ip)).start()
        # all_log = search_log(path, host_ip)
        all_log = log_file.objects.filter(path_2=path)
        return render(request, 'log_2.html', locals())


def log_info(request, name):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✔'
    path = run(host_ip, "root", "echo -n `find /var/log -name {}`".format(name)).decode('utf-8')
    log_type = run(host_ip, "root", "bash /root/shell/file_type.sh {}".format(path)).decode('utf-8')
    if log_type == 'ASCII':
        info = run(host_ip, "root", "cat {}".format(path)).decode('ascii')
    elif log_type == 'gzip':
        info = run(host_ip, "root", "zcat {}".format(path)).decode('utf-8')
    elif log_type == 'utf-8':
        info = run(host_ip, "root", "cat {}".format(path)).decode('utf-8')
    elif log_type == 'data':
        info = "此类型文件暂不支持查看！！！"
    else:
        info = run(host_ip, "root", "cat {}".format(path))
    return render(request, 'log_info.html', locals())


def search_log(path, host_ip):
    run(host_ip, "root", "nohup ls {} > /root/shell/log_file.txt &".format(path))
    files = run(host_ip, "root", "nohup cat /root/shell/log_file.txt &").decode('utf-8')

    # for f in log_file.objects.all():  # 检验是否有文件被删除
    #     check = int(run(host_ip, "root", "bash /root/shell/log_exist.sh {}".format(f.path)).decode('utf-8'))
    #     if check == 1:
    #         log_file.objects.get(path=f.path).delete()

    os.system("nohup mysql -u root -p{} -Dproject -e 'truncate log_file;' &".format(mysql_passwd))
    for file_name in files.splitlines():
        file_type = run(host_ip, "root", "nohup bash /root/shell/file_type.sh {}/{} &".format(path, file_name)).decode(
            'utf-8')
        # file_size = run(host_ip, "root", "bash /root/shell/file_size.sh {}/{}".format(path, file_name)).decode('utf-8')
        file_time = run(host_ip, "root", "nohup bash /root/shell/file_time.sh {} {} &".format(path, file_name)).decode(
            'utf-8')

        # try:
        #     file = log_file.objects.get(path="{}/{}".format(path, file_name))
        #     # 尝试获取该文件数据并更新文件大小
        #     if file_type != "directory":
        #         file.size = file_size
        #         file.time = file_time
        #     file.save()
        # except Exception as e:
        # if file_type == "directory":
        #     log_file.objects.create(name=file_name,
        #                             type=file_type,
        #                             path="{}/{}".format(path, file_name),
        #                             path_2=path)
        # else:
        log_file.objects.create(name=file_name,
                                # size=file_size,
                                type=file_type,
                                path="{}/{}".format(path, file_name),
                                path_2=path,
                                time=file_time)

    # all_log = log_file.objects.filter(path_2=path)
    # return all_log


######################################################################################
def backup(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    if not usr_name:
        return HttpResponseRedirect('/login')
    root_usr = users.objects.filter(is_root=True)
    usr_access = '✘'
    for n in root_usr:
        if usr_name == n.name:
            usr_access = '✔'
    if usr_access == '✘':
        ERROR = '当前用户不具备管理权限'
        return HttpResponseRedirect('/management')
    if request.method == 'GET':
        # if host_ip != localhost:
        #     ERROR = '该功能目前只支持本机 !'
        #     return render(request, 'backup_err.html', locals())
        # else:
        status = check_mission(host_ip)
        status_num = check_mission_num(host_ip)
        all_backup = backup_log.objects.filter(host=host_ip)
        return render(request, 'backup.html', locals())
    elif request.method == 'POST':
        if request.POST.get('file'):                                    # 刷新文件大小
            file_name = request.POST.get('file')
            path = run(host_ip, "root", "find /root -name {}".format(file_name)).decode('utf-8')
            file_size = run(host_ip, "root", "bash /root/shell/file_size.sh {}".format(path)).decode('utf-8')
            file = backup_log.objects.get(file=file_name, host=host_ip)
            file.size = file_size
            file.save()
            if file_size == file.size:
                check_num = 'ok'
                return JsonResponse({'file': file_name, 'size': file_size, 'check': check_num})
            else:
                return JsonResponse({'file': file_name, 'size': file_size})

        time = datetime.datetime.now()
        file_name = request.POST['file_name']
        exc1 = request.POST['exclude1']
        exc2 = request.POST['exclude2']
        exc3 = request.POST['exclude3']
        exc4 = request.POST['exclude4']
        exc5 = request.POST['exclude5']

        try:
            backup_log.objects.get(file=file_name, host=host_ip)
            all_backup = backup_log.objects.filter(host=host_ip)
            ERROR = "请避免备份文件名重复！！！"
            status = check_mission(host_ip)
            status_num = check_mission_num(host_ip)
            return render(request, 'backup.html', locals())
        except Exception as e:
            backup_log.objects.create(file=file_name,
                                      time=time.strftime("%Y-%m-%d %H:%M:%S"),
                                      path="~/",
                                      host=host_ip)

            def backup_task():
                # time.sleep(2)
                run(host_ip, "root", "tar cpzf {} --exclude={} --exclude={} --exclude={} --exclude={} --exclude={} /".format(file_name, exc1, exc2, exc3, exc4, exc5))

            #def backup_task_centos():

            threading.Thread(target=backup_task).start()

            status = check_mission(host_ip)
            status_num = check_mission_num(host_ip)
            # path = run(host_ip, "root", "find /root -name {} &".format(file_name)).decode('utf-8')
            all_backup = backup_log.objects.filter(host=host_ip)
            return render(request, 'backup.html', locals())


# def backup_2(func, host_ip, file_name, exc1, exc2, exc3, exc4, exc5):
#     def wrapper(*args, **kwargs):
#         def backup_task():
#             # time.sleep(2)
#             run(host_ip, "root", "nohup tar cvpzf {} --exclude={} --exclude={} --exclude={} --exclude={} --exclude={} / &".format(file_name, exc1, exc2, exc3, exc4, exc5))
#         threading.Thread(target=backup_task).start()
#         return func(*args, **kwargs)
#     return wrapper


def restore_backup(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    file_name = request.GET.get('file_name')
    if not usr_name:
        return HttpResponseRedirect('/login')
    run(host_ip, "root", "nohup tar xvpfz {} -C / &".format(file_name))
    n = check_mission()
    while n == 1:
        n = check_mission()
    mkdir("/proc"), mkdir("/sys"), mkdir("/mnt"), mkdir("/lost+found")
    return HttpResponseRedirect('/backup')


def delete_backup(request):
    usr_name = request.COOKIES.get('usr_name')
    host_ip = request.COOKIES.get('host_ip')
    file_name = request.GET.get('file_name')
    if not usr_name:
        return HttpResponseRedirect('/login')
    path = run(host_ip, "root", "find /root -name {}".format(file_name)).decode('utf-8')
    run(host_ip, "root", "rm -rf {}".format(path))
    file = backup_log.objects.get(file=file_name, host=host_ip)
    file.delete()
    return HttpResponseRedirect('/backup')


# def update_backup():
#     # usr_name = request.COOKIES.get('usr_name')
#     # host_ip = request.COOKIES.get('host_ip')
#     # file_name = request.GET.get('file_name')
#     # if not usr_name:
#     #     return HttpResponseRedirect('/login')
#     # path = run(host_ip, "root", "find /root -name {}".format(file_name)).decode('utf-8')
#     # file_size = run(host_ip, "root", "bash /root/shell/file_size.sh {}".format(path)).decode('utf-8')
#     # file = backup_log.objects.get(file=file_name)
#     # file.size = file_size
#     # file.save()
#     return HttpResponseRedirect('/backup')


def check_mission(host_ip):
    check = int(run(host_ip, "root", "ps -aux|grep 'tar cpzf'| wc -l"))
    if check == 2:
        status = "当前没有进行中的备份任务"
    else:
        num = check - 2
        status = "当前存在{}个进行中的备份任务！".format(num)
    return status


def check_mission_num(host_ip):
    check = int(run(host_ip, "root", "ps -aux|grep 'tar cpzf'| wc -l"))
    if check == 2:
        status_num = 0
    else:
        status_num = 1
    return status_num


def mkdir(dir, host_ip):
    i = run(host_ip, "root", "bash /root/shell/check_file.sh {}".format(dir)).decode('utf-8')
    if i == 0:
        run(host_ip, "root", "mkdir {}".format(dir))
    else:
        return


################################# Paramiko远程执行命令函数 ##################################################
def run(host_ip, user, cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host_ip, 22, user, timeout=20)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    ssh.close()
    return result
