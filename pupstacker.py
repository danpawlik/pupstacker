#!/usr/bin/env python3


import argparse
import configparser
import git
import glob
import json
import sys
import os

from oslo_config import cfg


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', help='Openstack project name')
    parser.add_argument('--project_url', help='Openstack project git url')
    parser.add_argument('--puppet-project',
                        help='Puppet Openstack project name. NOTE: if its '
                        'empty, it will use puppet-$PROJECT repo.')
    parser.add_argument('--puppet-project-url',
                        help='Puppet Openstack git project url')
    parser.add_argument('--workdir',
                        help='Set workdir, where projects will be cloned')
    return parser.parse_args()


def clone_project(project, workdir, project_url):
    git_url = (project_url if project_url else
               "https://github.com/openstack/%s" % project)
    project_dir = ("%s/%s" % (workdir, project))
    create_dir(project_dir)
    try:
        print("Cloning project %s to %s" % (git_url, project_dir))
        git.Repo.clone_from(git_url, project_dir)
        return project_dir
    except Exception as e:
        print("Problem occured on cloning %s" % project)
        print(e)


def execute_tox_genconfig(project_dir):
    print("Going to project dir and execute tox -e genconfig")
    command = "cd %s && tox -e genconfig" % project_dir
    execute_command(command)


def sed_on_file(sample_file):
    comment_cmd = ("sed -i /#\ /d %s" % sample_file)
    print("Executing %s" % comment_cmd)
    execute_command(comment_cmd)
    uncomment_cmd = "sed -i 's/#//g' %s" % sample_file
    print("Removing other useless chars: %s" % uncomment_cmd)
    execute_command(uncomment_cmd)
    new_line_cmd = ("sed -i '/^$/d' %s" % sample_file)
    print("Removing new lines chars: %s" % new_line_cmd)
    execute_command(new_line_cmd)


def execute_command(command):
    os.system(command)


def create_dir(dst_dir):
    print("Creating %s dir" % dst_dir)
    if not os.path.exists(dst_dir):
        try:
            os.makedirs(dst_dir)
        except Exception as e:
            print(e)


def get_sample_files(project_dir):
    print("Getting sample files...")
    sample_files = []
    generated_dir = "%s/etc/*.sample" % project_dir
    for sample in glob.glob(generated_dir):
        sample_files.append(sample)

    return sample_files


def filter_sample_files(sample_files):
    tmp_list = []
    for conf_file in sample_files:
        if 'conf' in conf_file:
            tmp_list.append(conf_file)

    return tmp_list


def cleanup_sample_files(sample_files):
    for sample in sample_files:
        sed_on_file(sample)


def get_params_from_section(section, conf):
    for namespace in conf._namespace._normalized[0]:
        if namespace == section:
            return conf._namespace._normalized[0].get(namespace)


def get_config_params(sample):
    # return a dict with section and params:
    # {SECTION: {param:value}}
    sample_conf = {}
    CONF = cfg.CONF
    CONF(['--config-file', sample])
    if CONF.list_all_sections():
        for section in CONF.list_all_sections():
            sample_conf['section'] = get_params_from_section(section, CONF)

    return sample_conf


def parse_sample_files(sample_files):
    print("Parsing sample files...")
    parsed_params = {}
    for sample in sample_files:
        config_name = os.path.basename(sample)
        parameters = get_config_params(sample)
        parsed_params[config_name] = parameters

    return parsed_params


if __name__ == "__main__":
    args = get_args()

    if not args.project:
        print("You need to set project arg")
        sys.exit(1)

    if not args.puppet_project:
        args.puppet_project = "puppet-%s" % args.project

    if not args.workdir:
        print("No workdir set. Using current dir")
        args.workdir = os.getcwd()

    # Cloning project url
    project_dir = clone_project(args.project, args.workdir, args.project_url)

    # Cloning puppet project url
    puppet_project_dir = clone_project(args.puppet_project, args.workdir,
                                       args.puppet_project_url)

    # Go to the project dir and execute
    execute_tox_genconfig(project_dir)

    # Find *.sample files in project/etc/*sample location
    project_dir = '/root/pupstacker/glance'
    sample_files = get_sample_files(project_dir)
    # remove ini, json, yaml files
    sample_files = filter_sample_files(sample_files)

    # Take all sample files and remove all lines that starts with '#<space> '
    if not sample_files:
        print("Can't find any sample files. Exit")
        os.exit(1)

    cleanup_sample_files(sample_files)

    # Create a dict with sample file configuration
    parsed_params = parse_sample_files(sample_files)
