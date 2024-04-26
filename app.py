from flask import Flask, render_template, request
import paramiko
import configparser

app = Flask(__name__)


config = configparser.ConfigParser()
config.read("config.ini", encoding='UTF-8')



@app.route('/')
def index():
    project_list = []
    for section in config.sections():
        project_list.append(section)
    return render_template('index.html', items=project_list)



@app.route('/project', methods=['POST'])
def execute():
    selected_item = request.form.get('item')
    project_name = selected_item
    servers_from_section = []
    for v in config.items(selected_item):
        servers_from_section.append(v[0])
    list_name_and_ip = config.items(selected_item)
    return render_template('project.html', items=servers_from_section, description=list_name_and_ip, project_name=project_name)


@app.route('/project/server', methods=['POST'])
def server():
    selected_item = request.form.get('item')
    project_name = request.form.get('projectPath')
    list_bcps = get_list_bcps(project_name, selected_item)
    list_bcps = list_bcps.split('\n')
    list_bcps = list_bcps[3:-1]
    for z in list_bcps:
        list_bcps[list_bcps.index(z)] = z[0:6] + '   -   ' + z[6:16] + '   time   ' + z[16:21] + z[21:27] +' status '+ z[27:29]
    return render_template('server.html', list_bcps=list_bcps, server_name = selected_item, project_name=project_name)

@app.route('/project/server/recovery', methods=['POST'])
def recovery():
    server_name = request.form.get('serverPath')
    project_name = request.form.get('projectPath')
    selected_item = request.form.get('bcp_id')
    server_ip = config[project_name][server_name]
    status = recovery_bcp(project_name,server_name,selected_item,server_ip)  
    return render_template('recovery.html', status = status)

    




def get_ip_server(item):
    with open('config.txt', 'r') as file:
        config_list = file.readlines()
        for i in config_list:
            if i.rsplit(':')[0] == item:
                return i.rsplit(':')[1]




def get_list_bcps(item, server):
    print("Выполняется функция 'sub' с элементом: ", item)
    k = paramiko.RSAKey.from_private_key_file(
        "C:\key")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname="ip", username="username", pkey=k)
    awk = "awk '{print $3 $4 $5 $15}'"
    commands = f"sudo pg_probackup-12 show -B /backups/{item}/probackup/ --instance {server} | {awk}"
    stdin, stdout, stderr = c.exec_command(commands)
    data = stdout.read() + stderr.read()
    c.close()
    return data.decode()




def recovery_bcp(project, server, id_bcp,server_ip):
    k = paramiko.RSAKey.from_private_key_file(
        "C:\key")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(hostname=server_ip, username="username", pkey=k)
    commands = f"sudo systemctl stop postgresql"
    stdin, stdout, stderr = c.exec_command(commands)
    data2 = stderr.read()
    if data2.decode() != '':
        return data2.decode()
    b = paramiko.SSHClient()
    b.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    b.connect(hostname='ip', username="username", pkey=k)
    command1 = f"sudo pg_probackup-12-std restore -B /backups/{project}/probackup/ --instance {server} -D /DATA/pgpro/std-15/data --remote-user=root --remote-host=10.97.100.111 --ssh-options='-o IdentityFile=/root/.ssh/key' -i {id_bcp}"
    stdin, stdout, stderr = b.exec_command(command1)
    data3 = stderr.read()
    if data3.decode() != '':
        return data3.decode()
    command2 = f"sudo systemctl start postgresql"
    stdin, stdout, stderr = c.exec_command(command2)
    data4 = stderr.read()
    if data4.decode() != '':
        return data4.decode()
    command3 = f"psql -h {server_ip} -c 'select 1;' postgres"
    stdin, stdout, stderr = b.exec_command(command3)
    data5 = stderr.read()
    if data5.decode() != '':
        return data5.decode()
    status = 'бэкап восстановлен'
    return status

if __name__ == '__main__':
    app.run(port=80)
