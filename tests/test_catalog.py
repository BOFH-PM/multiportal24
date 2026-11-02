import copy,importlib.util,pathlib,unittest,yaml
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalog',root/'scripts/catalog.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CatalogTest(unittest.TestCase):
 def setUp(self):self.data=yaml.safe_load((root/'catalog/apps.yml').read_text())
 def test_valid(self):self.assertEqual(len(m.render(self.data)[0]['application_routes']),4)
 def test_reserved_domains_and_injection(self):
  for v in ['rancher.multi.bofh.pm','api.multi.bofh.pm','zabbix.multi.bofh.pm','*.apps.multi.bofh.pm','x.apps.multi.bofh.pm\nbackend injected']:
   with self.subTest(v=v):
    d=copy.deepcopy(self.data);d['applications'][0]['domain']=v
    with self.assertRaises(ValueError):m.validate(d)
 def test_system_namespace(self):
  self.data['applications'][0]['namespace']='kube-system'
  with self.assertRaises(ValueError):m.validate(self.data)
 def test_ecosystem_namespaces(self):
  for namespace in ['bieszczady','bofh','intergol','oficyna','pbem','slezak','wspolnota']:
   with self.subTest(namespace=namespace):
    data=copy.deepcopy(self.data);data['applications'][0]['namespace']=namespace
    m.validate(data)
 def test_duplicate_host(self):
  self.data['applications'].append(self.data['applications'][0])
  with self.assertRaises(ValueError):m.validate(self.data)
 def test_port_not_boolean(self):
  self.data['applications'][0]['port']=True
  with self.assertRaises(ValueError):m.validate(self.data)
 def test_unknown_backend_ip_field(self):
  self.data['applications'][0]['ip']='127.0.0.1'
  with self.assertRaises(ValueError):m.validate(self.data)
 def test_optional_health_path(self):
  self.data['applications'][0]['health_path']='/healthz'
  routes,_=m.render(self.data)
  self.assertEqual(routes['application_routes'][0]['health_path'],'/healthz')
  for value in ['healthz','/health?token=x','/health\nbackend injected']:
   with self.subTest(value=value):
    data=copy.deepcopy(self.data);data['applications'][0]['health_path']=value
    with self.assertRaises(ValueError):m.validate(data)
 def test_duplicate_yaml_keys(self):
  with self.assertRaises(ValueError):yaml.load('version: 1\nversion: 2',Loader=m.Loader)
if __name__=='__main__':unittest.main()
