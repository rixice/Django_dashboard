# Generated by Django 2.2.12 on 2021-10-31 10:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kubernete', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='hosts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_ip', models.CharField(default='', max_length=50, verbose_name='主机IP')),
                ('host_name', models.CharField(default=models.CharField(default='', max_length=50, verbose_name='主机IP'), max_length=50, verbose_name='别名')),
            ],
            options={
                'db_table': 'hosts',
            },
        ),
    ]
