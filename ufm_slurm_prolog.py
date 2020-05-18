#!/usr/bin/python
"""
Created on July 7, 2019

@author: lioros
@copyright:
        Copyright (C) Mellanox Technologies Ltd. 2001-2017.  ALL RIGHTS RESERVED.

        This software product is a proprietary product of Mellanox Technologies Ltd.
        (the "Company") and all right, title, and interest in and to the software product,
        including all associated intellectual property rights, are and shall
        remain exclusively with the Company.

        This software product is governed by the End User License Agreement
        provided with the software product.
"""
import sys
import os
import time
from ufm_slurm_utils import UFM, GeneralUtils, Integration, Constants
import argparse
import subprocess
import logging

class UfmSlurmProlog:
    should_fail = 0 #set 0 the script will not fail; 1 the script will fail

    def init(self):
        self.ufm = UFM()
        self.general_utils = GeneralUtils()
        self.integration = Integration()
        conf_file = self.general_utils.getSlurmConfFile()
        if not self.general_utils.isFileExist(conf_file):
            logging.error(Constants.UFM_SLURM_CONF_NOT_EXIST %conf_file)
            sys.exit(self.should_fail)
        self.server = self.general_utils.read_conf_file(Constants.CONF_UFM_IP)
        self.user = self.general_utils.read_conf_file(Constants.CONF_UFM_USER)
        self.password = self.general_utils.read_conf_file(Constants.CONF_UFM_PASSWORD)
        self.log_name = self.general_utils.read_conf_file(Constants.CONF_LOGFILE_NAME)
        self.login_details = {"-u":self.user, "-p":self.password}
        self.device_list = []
        self.args = None
        self.sdk_ip = None

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--job_id", action="store",
                                    dest="job_id", default=None,
                                    help="Job ID")
        self.args = parser.parse_args(sys.argv[1:])


    def prolog_init(self):
        try:
            self.parse_args()
            format_str = "%(asctime)-15s  UFM-SLURM-Prolog JobID:" + self.args.job_id + "    %(levelname)-7s  : %(message)s"
            logging.basicConfig(format=format_str, level=logging.INFO, filename=self.log_name)
            logging.info("Start JobID: " + self.args.job_id)
            if not self.ufm.isRestSdkInstalled(self.sdk_ip):
                logging.error(Constants.LOG_SDK_NOT_INSTALLED)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error("error in prolog init function: %s" % str(exc) )
            sys.exit(self.should_fail)

    def connect_to_ufm(self):
        try:
            if not self.server:
                logging.error(Constants.UFM_ERR_PARSE_IP)
                sys.exit(self.should_fail)
            logging.info(Constants.LOG_CONNECT_UFM %self.server)
            is_running, msg = self.ufm.IsUfmRunning(self.server, self.sdk_ip, login_details=self.login_details)
            if is_running:
                logging.info(Constants.LOG_UFM_RUNNING %self.server)
            else:
                logging.error(Constants.LOG_CANNOT_UFM %msg)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error(Constants.LOG_ERROR_UFM_CONNECT % str(exc) )
            sys.exit(self.should_fail)

    def get_job_nodes(self):
        try:
            nodes_names = self.integration.getJobNodesName()
            nodes = nodes_names.splitlines()
            if not nodes:
                logging.error(Constants.LOG_CANNOT_GET_NODES)
                sys.exit(self.should_fail)
            hosts_guids = self.ufm.getHostnameHostGuidDictRestSDK(self.server, self.sdk_ip, login_details=self.login_details)
            if not hosts_guids:
                logging.error(Constants.LOG_CANNOT_GUID_NODES)
                sys.exit(self.should_fail)
            logging.info("The Job Nodes are:")
            add_related_hosts = self.general_utils.getAddRelatedHosts()
            for node in nodes:
                if node in hosts_guids.keys():
                    found = False
                    for guid in hosts_guids[node]:
                        self.device_list.append(guid)
                        found = True
                        if not add_related_hosts:
                            break
                    if found:
                        logging.info(node)
                    else:
                        logging.error(guid + Constants.LOG_GUID_NOT_FOUND)
                else:
                    logging.warning(node + Constants.LOG_NODE_NOT_FOUND)
            if not self.device_list:
                logging.error(Constants.LOG_NO_GUIDS_FOUND)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error(Constants.LOG_ERROR_GET_NODES % str(exc) )
            sys.exit(self.should_fail)

    def create_env(self):
        try:
            if self.ufm.getEnvironment(self.server, Constants.SLURM_ENV_NAME, self.sdk_ip, login_details=self.login_details) is None:
                logging.info(Constants.LOG_CREATE_ENV % Constants.SLURM_ENV_NAME)
                self.ufm.createEnvironment(self.server, Constants.SLURM_ENV_NAME, self.sdk_ip, login_details=self.login_details)
            if self.ufm.getEnvironment(self.server, Constants.SLURM_ENV_NAME, self.sdk_ip, login_details=self.login_details) is None:
                logging.error(Constants.LOG_FAIL_CREATE_ENV % Constants.SLURM_ENV_NAME)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error(Constants.LOG_ERROR_CREATE_ENV % (Constants.SLURM_ENV_NAME, str(exc)))
            sys.exit(self.should_fail)

    def create_ls(self):
        try:
            self.ls_name = '%s%s'%(Constants.LS_JOB_NAME, self.args.job_id)
            self.ufm.deleteLogicalServer(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.sdk_ip, login_details=self.login_details)
            logging.info(Constants.LOG_CREATE_LS % self.ls_name)
            if self.ufm.createLogicalServer(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.sdk_ip, login_details=self.login_details):
                logging.info(Constants.LOG_LS_CREATED % self.ls_name)
            else:
                logging.info(Constants.LOG_FAILED_CREATE_LS % self.ls_name)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error(Constants.LOG_ERROR_CREATE_LS % (self.ls_name, str(exc)))
            sys.exit(self.should_fail)
        
    def assign_nodes(self):
        try:
            logging.info(Constants.ALLOCATE_NODES)
            if not self.device_list:
                logging.error(Constants.LOG_ERR_ALLOCATE_NODES % self.ls_name)
                sys.exit(self.should_fail)
            status, error = self.ufm.allocateDevicesToLS(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.device_list, self.sdk_ip, login_details=self.login_details)
            if not status:
                logging.error(Constants.LOG_ERR_ALLOCATE % error)
                sys.exit(self.should_fail)
            is_all_exist, lst = self.ufm.isAllDevicesExistInLS(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.device_list, self.sdk_ip, login_details=self.login_details)
            if is_all_exist:
                logging.info(Constants.LOG_SUCCESS_ALLOCATION)
            else:
                logging.error(Constants.LOG_NOT_ALL_ALLOCATED)
                if lst:
                    logging.error(Constants.LOG_LST_NODES_NOT_ADDED)
                    for dev in lst:
                        logging.error(dev)
        except Exception, exc:
            logging.error(
            Constants.LOG_ERR_ALLOCATE % str(exc))
            sys.exit(self.should_fail)

if __name__ == '__main__':
    try:
        all_time_start = time.time()
        prolog = UfmSlurmProlog()
        prolog.init()
        prolog.prolog_init()
        prolog.connect_to_ufm()
        prolog.get_job_nodes()
        prolog.create_env()
        prolog.create_ls()
        prolog.assign_nodes()
        logging.info("UFM-Prolog time: %.1f seconds" % (time.time() - all_time_start))
    except Exception, exc:
        logging.error(
        Constants.LOG_ERR_PROLOG % str(exc))
        sys.exit(prolog.should_fail)    
    