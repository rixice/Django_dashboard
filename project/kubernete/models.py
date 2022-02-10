from django.db import models


# Create your models here.
class users(models.Model):
    name = models.CharField("用户名", max_length=50, default='')
    password = models.CharField("密码", max_length=50, default='')
    is_active = models.BooleanField('confirm to delete!', default=True)
    is_root = models.BooleanField('confirm its admin', default=False)

    class Meta:
        db_table = 'user_inf'


class hosts(models.Model):
    host_ip = models.CharField("主机IP", max_length=50, default='')
    host_name = models.CharField("别名", max_length=50, default=host_ip)
    host_status = models.CharField(max_length=10, default='')

    class Meta:
        db_table = 'hosts'


class name_spaces(models.Model):
    namespace = models.CharField("命名空间", max_length=50, default='')
    status = models.CharField('confirm to it is alive!', default='Active', max_length=50)

    class Meta:
        db_table = 'namespaces'


class pods(models.Model):
    namespace = models.CharField("命名空间", max_length=50, default='')
    pod_ip = models.CharField("Pods_IP", max_length=50, default='NotReady')
    pod_name = models.CharField("Pods_Name", max_length=100, default='')
    is_active = models.BooleanField('confirm to delete!', default=True)
    status = models.CharField("STATUS", default='', max_length=50)

    class Meta:
        db_table = 'pods'


class services(models.Model):
    kind = models.CharField("服务类型", max_length=50, default='None')
    namespace = models.CharField("命名空间", max_length=50, default='')
    spec_cluster_ip = models.CharField("Cluster_ip", max_length=50, default='')
    out_port = models.CharField("暴露端口", default='', max_length=100)
    in_port = models.CharField("占用端口", default='', max_length=100)
    service_name = models.CharField("服务名称", max_length=100, default='')
    is_active = models.BooleanField('confirm to delete!', default=True)

    class Meta:
        db_table = 'services'


class nodes(models.Model):
    name = models.CharField("节点名称", max_length=50, default='')
    status = models.CharField("节点状态", max_length=50, default='')

    class Meta:
        db_table = 'nodes'


class deploys(models.Model):
    name = models.CharField("依赖名称", max_length=200, default='')
    status = models.CharField("依赖状态", max_length=50, default='')
    age = models.CharField("存活时间", max_length=100, default='')
    namespace = models.CharField("所属命名空间", max_length=100, default='default')

    class Meta:
        db_table = 'deploys'


class log_file(models.Model):
    name = models.TextField("文件名", default='')
    path = models.CharField("文件路径", default='', max_length=255)
    path_2 = models.TextField("所属目录", default='')
    size = models.TextField("文件大小", default='')
    type = models.TextField("类型", default='')
    time = models.TextField("最后修改时间", default='')
    host = models.CharField("所属主机IP", default='', max_length=50)

    class Meta:
        db_table = 'log_file'


class backup_log(models.Model):
    file = models.CharField("备份文件名", default='', max_length=100)
    time = models.CharField("备份时间", default='', max_length=50)
    path = models.TextField("备份存放路径", default='')
    size = models.CharField("文件大小", default='', max_length=50)
    host = models.CharField("所在主机", default='', max_length=50)

    class Meta:
        db_table = 'backup_log'
