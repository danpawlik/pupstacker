#!/usr/bin/env python3


import argparse
import git
import glob
import sys
import os


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
    sample_files = []
    generated_dir = "%s/etc/*.sample" % project_dir
    for sample in glob.glob(generated_dir):
        sample_files.append(sample)

    return sample


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

    # Take all sample files and remove all lines that starts with '#<space> '
    sed_on_file('/root/pupstacker/glance/etc/glance-api.conf.sample')
