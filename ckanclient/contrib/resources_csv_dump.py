'''
Create a CSV dump of a CKAN instance, resource by resource.

Compare with the 'paster db simple-dump-csv' command which is one line per dataset (although it requires access to the CKAN machine).

Author: Friedrich
'''
import argparse
import ckanclient
import csv

parser = argparse.ArgumentParser(description=
    'Create a CSV dump of a CKAN instance, resource by resource.')
parser.add_argument('url', metavar='API_URL', type=str,
                    help='CKAN API endpoint')
parser.add_argument('outfile', metavar='OUTPUT_FILE', type=str,
                    help='output CSV file name')

def main():
    args = parser.parse_args()
    client = ckanclient.CkanClient(args.url)
    rows = []
    for pkg_name in client.package_register_get():
        pkg = client.package_entity_get(pkg_name)
        for extra, value in pkg.get('extras', {}).items():
            pkg['extras_' + extra] = value
        if 'extras' in pkg:
            del pkg['extras']
        resources = pkg.get('resources', [])
        for resource in resources:
            rpkg = pkg.copy()
            for resprop, value in resource.items():
                rpkg['resource_' + resprop] = value
            rows.append(rpkg)
        if not len(resources):
            rows.append(pkg)
        del pkg['resources']
        print pkg_name
    headers = set()
    for row in rows:
        headers.update(row.keys())
    fh = open(args.outfile, 'wb')
    writer = csv.DictWriter(fh, headers)
    writer.writerow(dict(zip(headers, headers)))
    for row in rows:
        row_ = {}
        for column, value in row.items():
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            row_[column] = value
        writer.writerow(row_)
    fh.close()

if __name__ == '__main__':
    main()
