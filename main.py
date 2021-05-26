#!/usr/bin/env python3

# Simple Python script to lookup EC2 instance ip addresses based on the name tag.

import os
import argparse
import boto3
from appdirs import user_cache_dir
from tabulate import tabulate

appname = "ec2query"
appauthor = "Haydar Ciftci"

cache_dir = user_cache_dir(appname, appauthor)


def get_regions():
    regions = []
    client = boto3.client('ec2')
    response = client.describe_regions()
    for region in response['Regions']:
        regions.append(region['RegionName'])

    return regions


def update():
    cache_file = cache_dir + os.path.sep + "awscache"
    regions = get_regions()

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    if os.path.exists(cache_file):
        os.unlink(cache_file)

    with open(cache_file, 'a') as cache_file_open:
        for region in regions:
            client_ec2 = boto3.client('ec2', region)
            client_rds = boto3.client('rds', region)

            reservations_ec2 = client_ec2.describe_instances()
            reservations_rds = client_rds.describe_db_instances()

            for reservation in reservations_ec2['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] != 'running':
                        continue

                    name = ""
                    for tag in instance['Tags']:
                        if tag['Key'] == 'Name':
                            name = tag['Value']

                    if instance['PrivateIpAddress']:
                        cache_file_open.write("{}\t{}\n".format(name.lower(), instance['PrivateIpAddress']))

            for instance in reservations_rds['DBInstances']:
                name = "-".join(instance['Endpoint']['Address'].split('-')[0:3]) + "-rds"
                cache_file_open.write("{}\t{}\n".format(name.lower(), instance['Endpoint']['Address']))

    print("Written cache to " + cache_file)


def search(name, update_cache=True):
    if not os.path.exists(cache_dir):
        update()

    cache_file = cache_dir + os.path.sep + "awscache"
    results = []

    for line in open(cache_file, 'r'):
        if line.find(name) > -1:
            results.append(line.strip().split("\t"))

    if len(results) == 0 and update_cache:
        update()
        return search(name, False)

    print(tabulate(results, headers=["Name", "Address"]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search for EC2 instances')
    parser.add_argument('name', type=str, nargs='?', help='Name of the EC2 instance')
    parser.add_argument('--update', action="store_true", help="Force update of cache")
    args = parser.parse_args()
    allow_auto_update = True

    if args.update:
        update()
        allow_auto_update = False

    search(str(args.name).lower(), allow_auto_update)
