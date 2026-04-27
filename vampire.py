# vampire.py
# API REST pour gerer des VM - projet VAMPIRE
# M1 SRC ESGI by SAMUEL

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import jwt
import datetime
import uuid
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vampire.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'cle_secrete_vampire_esgi'

db = SQLAlchemy(app)


# Modeles

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    api_key = db.Column(db.String(36), unique=True, nullable=False)


class VirtualMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    cpus = db.Column(db.Integer, default=1)
    ram_gb = db.Column(db.Integer, default=2)
    disks = db.Column(db.Text)   # stocke du JSON
    nics = db.Column(db.Text)    # stocke du JSON
    hypervisor = db.Column(db.String(200))
    status = db.Column(db.String(50), default='stopped')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'cpus': self.cpus,
            'ram_gb': self.ram_gb,
            'disks': json.loads(self.disks) if self.disks else {},
            'nics': json.loads(self.nics) if self.nics else [],
            'hypervisor': self.hypervisor,
            'status': self.status,
        }


# Init de la base avec quelques VMs en dur pour tester (V1)

def init_db():
    db.create_all()
    if User.query.count() > 0:
        return

    user = User(username='admin', password='admin123', api_key=str(uuid.uuid4()))
    db.session.add(user)
    db.session.flush()

    vms = [
        {
            'uuid': '41adb2b6-78f9-4179-ae0f-efdc0437b9a6',
            'name': 'P41_LINUX_RL_003',
            'title': 'RockyLinux 9.5 serveur Web projet 41',
            'description': 'Serveur web Nginx',
            'cpus': 2, 'ram_gb': 4,
            'disks': {'disk_1': 10, 'disk_2': 100},
            'nics': ['NIC_1', 'NIC_2'],
            'hypervisor': 'qemu+kvm://172.17.3.2',
            'status': 'running',
        },
        {
            'uuid': 'b2c3d4e5-f6a7-4b89-c0d1-e2f3a4b5c6d7',
            'name': 'P41_WIN_SRV_001',
            'title': 'Windows Server 2022 Active Directory',
            'description': 'Controleur de domaine principal',
            'cpus': 4, 'ram_gb': 8,
            'disks': {'disk_1': 60, 'disk_2': 200},
            'nics': ['NIC_1'],
            'hypervisor': 'qemu+kvm://172.17.3.3',
            'status': 'running',
        },
        {
            'uuid': 'c3d4e5f6-a7b8-4c9d-d0e1-f2a3b4c5d6e7',
            'name': 'P41_LINUX_DB_001',
            'title': 'Debian 12 - Serveur MariaDB',
            'description': 'Base de donnees principale du projet',
            'cpus': 2, 'ram_gb': 6,
            'disks': {'disk_1': 20, 'disk_2': 500},
            'nics': ['NIC_1', 'NIC_2'],
            'hypervisor': 'qemu+kvm://172.17.3.2',
            'status': 'stopped',
        },
    ]

    for v in vms:
        vm = VirtualMachine(
            uuid=v['uuid'],
            name=v['name'],
            title=v['title'],
            description=v['description'],
            cpus=v['cpus'],
            ram_gb=v['ram_gb'],
            disks=json.dumps(v['disks']),
            nics=json.dumps(v['nics']),
            hypervisor=v['hypervisor'],
            status=v['status'],
            user_id=user.id,
        )
        db.session.add(vm)
    db.session.commit()


with app.app_context():
    init_db()


# Decorateur pour proteger les routes avec JWT

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return jsonify({'error': 'Token manquant'}), 401
        try:
            token = auth.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = db.session.get(User, data['user_id'])
            if not user:
                return jsonify({'error': 'Token invalide'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expire'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        return f(user, *args, **kwargs)
    return decorated


# Routes auth

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'username et password requis'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Utilisateur deja existant'}), 409

    user = User(username=username, password=password, api_key=str(uuid.uuid4()))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Utilisateur cree', 'api_key': user.api_key}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username'), password=data.get('password')).first()
    if not user:
        return jsonify({'error': 'Identifiants invalides'}), 401

    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token})


# Routes CRUD VMs

@app.route('/api/vms', methods=['POST'])
@token_required
def create_vm(current_user):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Le champ name est requis'}), 400

    vm = VirtualMachine(
        uuid=str(uuid.uuid4()),
        name=data.get('name'),
        title=data.get('title'),
        description=data.get('description'),
        cpus=data.get('cpus', 1),
        ram_gb=data.get('ram_gb', 2),
        disks=json.dumps(data.get('disks', {})),
        nics=json.dumps(data.get('nics', [])),
        hypervisor=data.get('hypervisor'),
        status='stopped',
        user_id=current_user.id
    )
    db.session.add(vm)
    db.session.commit()
    return jsonify({'message': 'VM creee', 'vm': vm.to_dict()}), 201


@app.route('/api/vms', methods=['GET'])
@token_required
def list_vms(current_user):
    vms = VirtualMachine.query.filter_by(user_id=current_user.id).all()
    return jsonify({'vms': [vm.to_dict() for vm in vms]})


@app.route('/api/vms/<int:vm_id>', methods=['GET'])
@token_required
def get_vm(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    return jsonify({'vm': vm.to_dict()})


@app.route('/api/vms/<int:vm_id>', methods=['PUT'])
@token_required
def update_vm(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404

    data = request.get_json()
    if 'name' in data:
        vm.name = data['name']
    if 'title' in data:
        vm.title = data['title']
    if 'description' in data:
        vm.description = data['description']
    if 'cpus' in data:
        vm.cpus = data['cpus']
    if 'ram_gb' in data:
        vm.ram_gb = data['ram_gb']
    if 'disks' in data:
        vm.disks = json.dumps(data['disks'])
    if 'nics' in data:
        vm.nics = json.dumps(data['nics'])
    if 'hypervisor' in data:
        vm.hypervisor = data['hypervisor']

    db.session.commit()
    return jsonify({'message': 'VM mise a jour', 'vm': vm.to_dict()})


@app.route('/api/vms/<int:vm_id>', methods=['DELETE'])
@token_required
def delete_vm(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    db.session.delete(vm)
    db.session.commit()
    return jsonify({'message': 'VM supprimee'})


# Actions sur les VMs

@app.route('/api/vms/<int:vm_id>/power_on', methods=['POST'])
@token_required
def power_on(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    if vm.status == 'running':
        return jsonify({'error': 'VM deja en cours'}), 400
    vm.status = 'running'
    db.session.commit()
    return jsonify({'message': 'VM ' + vm.name + ' demarree', 'status': vm.status})


@app.route('/api/vms/<int:vm_id>/power_off', methods=['POST'])
@token_required
def power_off(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    if vm.status == 'stopped':
        return jsonify({'error': 'VM deja arretee'}), 400
    vm.status = 'stopped'
    db.session.commit()
    return jsonify({'message': 'VM ' + vm.name + ' arretee', 'status': vm.status})


@app.route('/api/vms/<int:vm_id>/suspend', methods=['POST'])
@token_required
def suspend(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    if vm.status != 'running':
        return jsonify({'error': 'La VM doit etre running pour etre suspendue'}), 400
    vm.status = 'suspended'
    db.session.commit()
    return jsonify({'message': 'VM ' + vm.name + ' suspendue', 'status': vm.status})


@app.route('/api/vms/<int:vm_id>/snapshot', methods=['POST'])
@token_required
def snapshot(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    data = request.get_json() or {}
    snap_name = data.get('snapshot_name', 'snap_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    return jsonify({'message': 'Snapshot cree pour ' + vm.name, 'snapshot_name': snap_name}), 201


@app.route('/api/vms/<int:vm_id>/backup', methods=['POST'])
@token_required
def backup(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    return jsonify({'message': 'Sauvegarde lancee pour ' + vm.name, 'backup_id': str(uuid.uuid4())}), 202


@app.route('/api/vms/<int:vm_id>/migrate', methods=['POST'])
@token_required
def migrate(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    data = request.get_json() or {}
    target = data.get('target_hypervisor')
    if not target:
        return jsonify({'error': 'target_hypervisor requis'}), 400
    old = vm.hypervisor
    vm.hypervisor = target
    db.session.commit()
    return jsonify({'message': 'VM ' + vm.name + ' migree', 'from': old, 'to': target})


@app.route('/api/vms/<int:vm_id>/status', methods=['GET'])
@token_required
def get_status(current_user, vm_id):
    vm = VirtualMachine.query.filter_by(id=vm_id, user_id=current_user.id).first()
    if not vm:
        return jsonify({'error': 'VM introuvable'}), 404
    return jsonify({'id': vm.id, 'name': vm.name, 'status': vm.status, 'hypervisor': vm.hypervisor})


# Recherche par criteres

@app.route('/api/vms/search', methods=['GET'])
@token_required
def search_vms(current_user):
    query = VirtualMachine.query.filter_by(user_id=current_user.id)

    name = request.args.get('name')
    status = request.args.get('status')
    hypervisor = request.args.get('hypervisor')
    cpus = request.args.get('cpus')
    ram_gb = request.args.get('ram_gb')

    if name:
        query = query.filter(VirtualMachine.name.ilike('%' + name + '%'))
    if status:
        query = query.filter(VirtualMachine.status == status)
    if hypervisor:
        query = query.filter(VirtualMachine.hypervisor.ilike('%' + hypervisor + '%'))
    if cpus:
        query = query.filter(VirtualMachine.cpus == int(cpus))
    if ram_gb:
        query = query.filter(VirtualMachine.ram_gb == int(ram_gb))

    vms = query.all()
    return jsonify({'results': [vm.to_dict() for vm in vms], 'count': len(vms)})


if __name__ == '__main__':
    app.run(debug=True)
