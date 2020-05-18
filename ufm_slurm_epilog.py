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
import argparse
import logging
from ufm_slurm_utils import UFM, GeneralUtils, Integration, Constants

class UfmSlurmEpilog():
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
        self.args = None
        self.sdk_ip = None

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--job_id", action="store",
                                    dest="job_id", default=None,
                                    help="Job ID")
        self.args = parser.parse_args(sys.argv[1:])

    def epilog_init(self):
        try:
            self.parse_args()
            format_str = "%(asctime)-15s  UFM-SLURM-Epilog JobID:" + self.args.job_id + "    %(levelname)-7s  : %(message)s"
            logging.basicConfig(format=format_str, level=logging.INFO, filename=self.log_name)
            if not self.ufm.isRestSdkInstalled(self.sdk_ip):
                logging.error(Constants.LOG_SDK_NOT_INSTALLED)
                sys.exit(self.should_fail)
        except Exception, exc:
            logging.error("error in epilog init function: %s" % str(exc) )
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


    def remove_ls(self):
        try:
            self.ls_name = '%s%s'%(Constants.LS_JOB_NAME, self.args.job_id)
            logging.info(Constants.LOG_REMOVE_LS)
            if self.ufm.isLogicalServerExist(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.sdk_ip, login_details=self.login_details):
                if self.ufm.deleteLogicalServer(self.server, Constants.SLURM_ENV_NAME, self.ls_name, self.sdk_ip, login_details=self.login_details):
                    logging.info(Constants.LOG_LS_REMOVED_SUCC % self.ls_name)
                else:
                    logging.error(Constants.LOG_LS_NOT_REMOVED % self.ls_name)
            else:
                logging.error(Constants.LOG_LS_NOT_EXIST_REMOVE % self.ls_name)
        except Exception as exc:
            logging.error(Constants.LOG_LS_ERR_REMOVE % self.ls_name)
            sys.exit(self.should_fail)

if __name__ == '__main__':
    try:
        epilog = UfmSlurmEpilog()
        epilog.init()
        epilog.epilog_init()
        epilog.connect_to_ufm()
        epilog.remove_ls()
    except Exception as exc:
        logging.error(
        Constants.LOG_ERR_EPILOG % str(exc))
        sys.exit(epilog.should_fail)  
    finally:
        logging.info("## Done ##")
