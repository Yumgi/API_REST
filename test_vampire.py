# test_vampire.py
# Script de validation de l'API VAMPIRE
# Lance les requetes sur les differentes URL pour verifier le fonctionnement

import requests
import json

BASE_URL = 'http://localhost:5000/api'


def afficher(titre, r):
    print('---', titre, '---')
    print('Status:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except:
        print(r.text)
    print()


# 1. Login avec le compte admin cree par init_db
print('=== 1. LOGIN ADMIN ===')
r = requests.post(BASE_URL + '/login', json={
    'username': 'admin',
    'password': 'admin123'
})
afficher('Login admin', r)
token = r.json()['token']
headers = {'Authorization': 'Bearer ' + token}


# 2. Creation d'un nouvel utilisateur (peut deja exister si script relance)
print('=== 2. REGISTER ===')
r = requests.post(BASE_URL + '/register', json={
    'username': 'samuel',
    'password': 'test123'
})
afficher('Creation user samuel', r)


# 3. Login avec un mauvais mot de passe (doit echouer)
print('=== 3. LOGIN AVEC MAUVAIS MDP ===')
r = requests.post(BASE_URL + '/login', json={
    'username': 'admin',
    'password': 'mauvais_mdp'
})
afficher('Login KO attendu', r)


# 4. Acces sans token (doit echouer)
print('=== 4. ACCES SANS TOKEN ===')
r = requests.get(BASE_URL + '/vms')
afficher('Acces refuse attendu', r)


# 5. Liste des VMs de admin (3 VMs en dur)
print('=== 5. LISTE DES VMs ===')
r = requests.get(BASE_URL + '/vms', headers=headers)
afficher('Liste VMs admin', r)


# 6. Creation d'une nouvelle VM
print('=== 6. CREATION VM ===')
new_vm = {
    'name': 'TEST_VM_001',
    'title': 'VM de test',
    'description': 'VM creee par le script de validation',
    'cpus': 2,
    'ram_gb': 4,
    'disks': {'disk_1': 20, 'disk_2': 50},
    'nics': ['NIC_1'],
    'hypervisor': 'qemu+kvm://172.17.3.4'
}
r = requests.post(BASE_URL + '/vms', headers=headers, json=new_vm)
afficher('Creation VM', r)
vm_id = r.json()['vm']['id']
print('VM creee avec id =', vm_id)
print()


# 7. Recuperer la VM par son id
print('=== 7. GET VM ===')
r = requests.get(BASE_URL + '/vms/' + str(vm_id), headers=headers)
afficher('Get VM', r)


# 8. Mise a jour de la VM
print('=== 8. UPDATE VM ===')
r = requests.put(BASE_URL + '/vms/' + str(vm_id), headers=headers, json={
    'cpus': 4,
    'ram_gb': 8,
    'description': 'VM mise a jour par le test'
})
afficher('Update VM', r)


# 9. Power on (stopped -> running)
print('=== 9. POWER ON ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/power_on', headers=headers)
afficher('Power on', r)


# 10. Power on a nouveau (doit echouer car deja running)
print('=== 10. POWER ON DOUBLON ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/power_on', headers=headers)
afficher('Erreur attendue', r)


# 11. Interrogation du status
print('=== 11. STATUS ===')
r = requests.get(BASE_URL + '/vms/' + str(vm_id) + '/status', headers=headers)
afficher('Status', r)


# 12. Suspend (running -> suspended)
print('=== 12. SUSPEND ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/suspend', headers=headers)
afficher('Suspend', r)


# 13. Snapshot
print('=== 13. SNAPSHOT ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/snapshot', headers=headers, json={
    'snapshot_name': 'snap_test_validation'
})
afficher('Snapshot', r)


# 14. Backup
print('=== 14. BACKUP ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/backup', headers=headers)
afficher('Backup', r)


# 15. Migration
print('=== 15. MIGRATION ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/migrate', headers=headers, json={
    'target_hypervisor': 'qemu+kvm://172.17.3.99'
})
afficher('Migration', r)


# 16. Power off (suspended -> stopped)
print('=== 16. POWER OFF ===')
r = requests.post(BASE_URL + '/vms/' + str(vm_id) + '/power_off', headers=headers)
afficher('Power off', r)


# 17. Recherche - tests des criteres
print('=== 17. RECHERCHES ===')

r = requests.get(BASE_URL + '/vms/search?status=running', headers=headers)
afficher('VMs running', r)

r = requests.get(BASE_URL + '/vms/search?cpus=2', headers=headers)
afficher('VMs avec 2 CPUs', r)

r = requests.get(BASE_URL + '/vms/search?name=LINUX', headers=headers)
afficher('VMs avec LINUX dans le nom', r)

r = requests.get(BASE_URL + '/vms/search?hypervisor=172.17.3.2', headers=headers)
afficher('VMs sur l hyperviseur 172.17.3.2', r)

r = requests.get(BASE_URL + '/vms/search?ram_gb=8', headers=headers)
afficher('VMs avec 8 Go de RAM', r)


# 18. Test isolation : samuel ne doit pas voir les VMs de admin
print('=== 18. ISOLATION DES UTILISATEURS ===')
r = requests.post(BASE_URL + '/login', json={
    'username': 'samuel',
    'password': 'test123'
})
token_samuel = r.json()['token']
headers_samuel = {'Authorization': 'Bearer ' + token_samuel}

r = requests.get(BASE_URL + '/vms', headers=headers_samuel)
afficher('Liste VMs de samuel (doit etre vide)', r)

# samuel essaye d acceder a la VM de admin
r = requests.get(BASE_URL + '/vms/' + str(vm_id), headers=headers_samuel)
afficher('Samuel essaye d acceder a la VM de admin (404 attendu)', r)


# 19. Suppression de la VM de test
print('=== 19. DELETE VM ===')
r = requests.delete(BASE_URL + '/vms/' + str(vm_id), headers=headers)
afficher('Delete VM', r)


# 20. Verifier que la VM n existe plus
print('=== 20. GET VM supprimee ===')
r = requests.get(BASE_URL + '/vms/' + str(vm_id), headers=headers)
afficher('Get VM supprimee (404 attendu)', r)


print('=== FIN DES TESTS ===')
