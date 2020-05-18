#!/usr/bin/python
"""
Created on July 7, 2019

@author: lioros
@copyright:
        Copyright (C) Mellanox Technologies Ltd. 2001-2019.  ALL RIGHTS RESERVED.

        This software product is a proprietary product of Mellanox Technologies Ltd.
        (the "Company") and all right, title, and interest in and to the software product,
        including all associated intellectual property rights, are and shall
        remain exclusively with the Company.

        This software product is governed by the End User License Agreement
        provided with the software product.
"""
import os
import re
import subprocess
import sys
import json

class Constants:
    SLURM_DEF_PATH = '/etc/slurm-llnl'
    UFM_SLURM_CONF_NAME = 'ufm_slurm.conf'
    SLURM_SERVICE_PATH = '/lib/systemd/system/slurmctld.service' 
    SDK_DEF_BASE_DIR = '/opt/ufmrestsdk/'
    SDK_UBUNTU_BASE = '/usr/opt/ufmrestsdk/' 
    SDK_BASE_DIR = SDK_DEF_BASE_DIR if os.path.exists(SDK_DEF_BASE_DIR) else SDK_UBUNTU_BASE
    CONF_UFM_IP = 'ufm_server'
    CONF_UFM_USER = 'ufm_server_user'
    CONF_UFM_PASSWORD = 'ufm_server_pass'
    CONF_PROTOCOL = "protocol"
    CONF_LOGFILE_NAME= 'log_file_name'
    CONF_ADD_RELATED_HOSTS = 'add_related_nics'
    ENVIRONMENTS_MODULE = 'environments'
    SYSTEMS_MODULE = 'systems'
    SERVERS_MODULE = 'servers'
    COMPUTES_MODULE = 'computes'
    LS_JOB_NAME = 'slurm_job_'
    SLURM_ENV_NAME = 'slurm_env'
    UFM_SLURM_CONF_NOT_EXIST = 'UFM-SLURM configuration file is not found. Check the path: %s'
    UFM_NOT_RESPONDING = 'UFM server is not responding'
    UFM_NOT_AVAILABLE = 'UFM is not available'
    UFM_AUTH_ERROR = 'Could not reach UFM. Check the authentication info.'
    UFM_CONNECT_ERROR = 'Could not reach/connect to UFM.'
    UFM_ERR_PARSE_IP = 'Cannot parse UFM IP Address'
    LOG_CONNECT_UFM = 'Connecting to UFM server ... %s'
    LOG_UFM_RUNNING = 'UFM: %s is running..'
    LOG_CANNOT_UFM = 'Cannot connect to the UFM server. %s'
    LOG_SDK_NOT_INSTALLED = 'UFM REST SDK is not installed on SLURM Controller machine.'
    LOG_CANNOT_GET_NODES = 'Could not get nodes of the job.'
    LOG_CANNOT_GUID_NODES = 'Could not get GUID of the job nodes.'
    LOG_GUID_NOT_FOUND = ' guid is not found in UFM fabric. It could not be added to the logical server.'
    LOG_NODE_NOT_FOUND = ' is not part of the UFM fabric. It could not be added to the logical server.'
    LOG_NO_GUIDS_FOUND = 'No GUIDS of nodes are found to add.'
    LOG_CREATE_ENV = 'Creating environment %s ...'
    LOG_FAIL_CREATE_ENV = 'Failed to create environment: %s'
    LOG_ERROR_CREATE_ENV = 'Error in creating Environment %s: %s'
    ALLOCATE_NODES = 'Allocate nodes to LS'
    LOG_ERR_ALLOCATE_NODES = 'Error in allocate nodes to LS %s: No nodes related to UFM server are found.'
    LOG_SUCCESS_ALLOCATION = 'Success. The allocation of the nodes to LS is passed'
    LOG_CREATE_LS = 'Creating logical server: %s ...'
    LOG_LS_CREATED = 'LS %s is created.'
    LOG_FAILED_CREATE_LS = 'Failed to create LS: %s.'
    LOG_ERROR_CREATE_LS = 'Error in creating LS %s: %s'
    LOG_NOT_ALL_ALLOCATED = 'Not all the nodes are allocated to the logical server.'
    LOG_LST_NODES_NOT_ADDED = 'The following nodes are not added:'
    LOG_ERR_ALLOCATE =  'Error in allocating nodes to LS. %s'
    LOG_ERROR_GET_NODES = 'Error in getting nodes: %s'
    LOG_ERROR_UFM_CONNECT = 'Error in connecting to the UFM: %s'
    LOG_ERR_PROLOG = 'Error during executing ufm prolog: %s'
    LOG_ERR_EPILOG = 'Error during executing ufm epilog: %s'
    LOG_REMOVE_LS = 'Removing LS..'
    LOG_LS_REMOVED_SUCC = 'Logical Server: %s is removed successfully'
    LOG_LS_NOT_REMOVED = 'LS: %s is not removed'
    LOG_LS_NOT_EXIST_REMOVE = 'LS: %s is not exist to be removed'
    LOG_LS_ERR_REMOVE = 'Error in removing LS: %s'
    ERROR_503 = '503 service temporarily unavailable'
    ERROR_401 = 'error 401'
    NOT_FOUND = 'not found'
    ERROR = "error"
    BAD_REQUEST = "400 BAD REQUEST"
    ERROR_404 = "404 NOT FOUND"
class GeneralUtils:

    def run_cmd(self, command, verbose=True):
        """
        Run Shell command.
        Direct output to subprocess.PIPE.
        Return command exit code, stdout and stderr.
        """
        proc = subprocess.Popen(command, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        return (proc.returncode, stdout.strip(), stderr.strip())

    def getSlurmConfFile(self):
        cmd = 'cat %s | grep ConditionPathExists'%Constants.SLURM_SERVICE_PATH
        ret, path, _ = self.run_cmd(cmd)
        if ret==0 and path:
            path = path.split("=")[1]
            return "%s/%s" %(os.path.dirname(path),Constants.UFM_SLURM_CONF_NAME)
        else:
            return "%s/%s" %(Constants.SLURM_DEF_PATH, Constants.UFM_SLURM_CONF_NAME)

    def read_conf_file(self, key):
        conf_file = self.getSlurmConfFile()
        file = open(conf_file, 'r')
        confs = file.read()
        match = re.search(r'%s.*=(.*)' % key, confs)
        if match:
            return match.groups()[0]
        else:
            return None

    def isFileExist(self, file_name):
        if os.path.exists(file_name):
            return True
        else:
            return False
    
    def getAddRelatedHosts(self):
        add_related = self.read_conf_file(Constants.CONF_ADD_RELATED_HOSTS)
        if add_related is not None:
            if "false" in add_related.lower():
                return False
        return True

class UFM:
    utils=GeneralUtils()
    def IsUfmRunning(self, ufm_server, ufm_sdk_server, login_details):
        """
        Check if UFM is running on a given device.
        """
        query = "get_all"
        sdk_module = Constants.SYSTEMS_MODULE

        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, systems, _ = self.runSdk(ufm_server, sdk_module, query, sdk_server=ufm_sdk_server, sdk_params=None, login_details=login_details)
        if not systems:
            return False, Constants.UFM_NOT_RESPONDING
        try:
            systems = json.loads(systems, strict=False)
            return True,""
        except Exception as ec:
            if Constants.ERROR_503 in systems.lower():
                return False, Constants.UFM_NOT_AVAILABLE
            elif Constants.ERROR_401 in systems.lower():
                return False, Constants.UFM_AUTH_ERROR
            else:
                return False, Constants.UFM_CONNECT_ERROR
    
    def getHostnameHostGuidDictRestSDK(self, ufm_server, ufm_sdk_server, login_details):
        query = "get_all"
        sdk_module = Constants.SYSTEMS_MODULE
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        hosts_dict = {}
        _, systems, _ = self.runSdk(ufm_server, sdk_module, query, sdk_server=ufm_sdk_server, sdk_params=None, login_details=login_details)
        if not systems:
            return hosts_dict
        systems = json.loads(systems, strict=False)
        systems = [sys for sys in systems if sys["type"] =="host"]
        for sys in systems:
            host_guid = sys["name"]
            host_name = sys["system_name"].split(" ")[0]
            if host_name not in hosts_dict:
                hosts_dict[host_name]=[]
            hosts_dict[host_name].append(host_guid)
        return hosts_dict

    def getDevicesInLS(self, ufm_server, env_name, ls_name, ufm_sdk_server, login_details):
        query = "get_all"
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        sdk_params = {"environment": env_name, "logical_server":ls_name}
        _, out, _ = self.runSdk(ufm_server, Constants.COMPUTES_MODULE, query, sdk_server=ufm_sdk_server, sdk_params=sdk_params, login_details=login_details)
        return json.loads(out, strict=False)
    
    def isAllDevicesExistInLS(self, ufm_server, env_name, ls_name, device_names_added, ufm_sdk_server, login_details):
        device_list = self.getDevicesInLS(ufm_server, env_name, ls_name, ufm_sdk_server, login_details=login_details)
        device_list = [dev["name"] for dev in device_list]
        not_included = []
        if device_list:
            not_included = list(set(device_names_added) - set(device_list))
            if not_included:
                return False, not_included
        else:
            return False, device_names_added
        return True, None
    
    def getLogicalServer(self, ufm_server, env_name, ls_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        query = "get" if ls_name else "get_all"
        sdk_params = {"environment": env_name}
        if ls_name:
            sdk_params["name"] = ls_name
        _, out, _ = self.runSdk(ufm_server, Constants.SERVERS_MODULE, query, sdk_server=ufm_sdk_server, sdk_params=sdk_params, login_details=login_details)
        if Constants.NOT_FOUND not in out.lower():
            return json.loads(out, strict=False)


    def isLogicalServerExist(self, ufm_server, env_name, ls_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        out = self.getLogicalServer(ufm_server, env_name, ls_name, ufm_sdk_server=ufm_sdk_server, login_details=login_details)
        if out:
            return True
        return False
    
    def createLogicalServer(self, ufm_server, env_name, ls_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, out, _ = self.runSdk(ufm_server, Constants.SERVERS_MODULE, "create", ufm_sdk_server, sdk_params={"environment":env_name, "name":ls_name}, login_details=login_details)
        return out

    def deleteLogicalServer(self, ufm_server, env_name, ls_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        if self.isLogicalServerExist(ufm_server, env_name, ls_name, ufm_sdk_server, login_details=login_details):
            _, out, _ = self.runSdk(ufm_server, Constants.SERVERS_MODULE, "delete", sdk_server=ufm_sdk_server, sdk_params={"environment":env_name, "name":ls_name}, login_details=login_details)
            if Constants.ERROR in out:
                return False
            else:
                return True
        else:
            return False

    def allocateDevicesToLS(self, ufm_server, env_name, ls_name, device_list, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, out, _ = self.runSdk(ufm_server, Constants.SERVERS_MODULE, "allocate-computes-manually", ufm_sdk_server, sdk_params={"environment":env_name, "name":ls_name, "computes":device_list}, login_details=login_details)
        if Constants.BAD_REQUEST in out or Constants.ERROR_404 in out:
            return False, out
        return True, None

    def getEnvironment(self, ufm_server, env_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, out, _ = self.runSdk(ufm_server, Constants.ENVIRONMENTS_MODULE, "get", sdk_server=ufm_sdk_server, sdk_params={"name":env_name}, login_details=login_details)
        if not Constants.NOT_FOUND in out.lower():
            return json.loads(out, strict=False)

    def createEnvironment(self, ufm_server, env_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, out, _ = self.runSdk(ufm_server, Constants.ENVIRONMENTS_MODULE, "create", ufm_sdk_server, sdk_params={"name":env_name}, login_details=login_details)
        return out

    def isSystemExist(self, ufm_server, system_guid_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        out = self.getSystem(ufm_server, system_guid_name, ufm_sdk_server=ufm_sdk_server, login_details=login_details)
        if out:
            return True
        return False

    def getSystem(self, ufm_server, system_guid_name, ufm_sdk_server, login_details):
        if not ufm_sdk_server:
            ufm_sdk_server = ufm_server
        _, out, _ = self.runSdk(ufm_server, Constants.SYSTEMS_MODULE, "get", sdk_server=ufm_sdk_server, sdk_params={"name":system_guid_name}, login_details=login_details)
        if not Constants.NOT_FOUND in out.lower():
            return json.loads(out, strict=False)

    def runSdk(self, ufm_server,
            sdk_name,
            sdk_option,
            sdk_server=None,
            login_details=None,
            protocol="https",
            sdk_params={},
            sdk_payload={},
            extra_options={}):

        """
        @param ufm_server: UFM server IP address

        @param sdk_name: Name of UFM SDK, please refer to
                        available SDK names in constants
                        file: sdk_constants.Sdk

        @param sdk_server: Server to run SDK script

        @param login_details: Username and Password info
                            as Dictionary:
                            {
                            "-u": "user",
                            "-p": "pass"
                            }

        @param protocol: can be either http or https, by
                        default it takes http.

        @param sdk_option: Each SDK has a set of available
                        options pre-defined in constants
                        file. Please refer to sdk_constants
                        to see available options for each
                        SDK.

        @param sdk_params: parameters required by certain
                        options such as "get" option you
                        need to specify group_id or maybe
                        event_id etc.

                        Examples:
                        1) One parameter with one value:
                            {"job_id": "7"}
                        2) One Parameter with multiple values:
                            {"element_id": ["5", "11", ...]}

        @param sdk_payload: payload required by certain options
                            such as "add" option.

                            Examples:
                            {"elementName":"group1",
                            "description":"testing groups"}
        """
        sdk_path = os.path.join(Constants.SDK_BASE_DIR, "%s.pyc"%sdk_name)
        user = self.utils.read_conf_file(Constants.CONF_UFM_USER)
        password = self.utils.read_conf_file(Constants.CONF_UFM_PASSWORD)
        login_details = {"-u":user, "-p":password}
        login_info = ""
        for key, value in login_details.iteritems():
            login_info += " %s %s" % (key, value)
        protocol = self.utils.read_conf_file(Constants.CONF_PROTOCOL)
        if not protocol:
            protocol = "https"
        sdk_command_line = "python {sdk_path} -s {ufm_server} {login_info}"\
            " -r {protocol} {sdk_option}"\
            .format(**locals())
        # Extract SDK Parameters
        if sdk_params:

            params_list = []
            all_params = ""
            for key, value in sdk_params.iteritems():
                if type(value) is list:
                    params_list.append("--%s=%s" % (key, ",".join(value)))
                else:
                    params_list.append("--%s=%s" % (key, value))
            if len(params_list) > 1:
                all_params = " ".join(params_list)
            else:
                all_params = params_list[0]

            sdk_command_line += " " + all_params

        # Extract SDK Payload
        if sdk_payload:
            payload = " --payload=\""
            payload_list = []
            all_payload = ""
            for key, value in sdk_payload.iteritems():
                if type(value) is list:
                    payload_list.append("%s=%s" % (key, ",".join(value)))
                else:
                    payload_list.append("%s=%s" % (key, value))
            if len(payload_list) > 1:
                all_payload = "&".join(payload_list)
            else:
                all_payload = payload_list[0]
            payload += all_payload
            payload += "\""
            sdk_command_line += payload

        # Extract Extra Options
        if extra_options:
            extra_options_info = ""
            for key, value in extra_options.iteritems():
                parsed_val = "\"{0}\"".format(value)
                extra_options_info += " %s %s" % (key, parsed_val)
            sdk_command_line += extra_options_info
        return self.utils.run_cmd(sdk_command_line, verbose=True)

    def parseSdkOutput(self, sdk_output):
        """
        @summary: Parses and extracts data from UFM SDK
                Output string (a.k.a execution log)

        @return: If sdk_output was parsed successfully
                returns a tuple of (status_code, result)
                If parsing fails returns None.
        """
        status_code = None
        sdk_result = None

        search_result = re.search("\[\*\][\s\S]*results:((?:[\S\s]*\n)+)", sdk_output)

        if search_result is not None:
            result = search_result.group(1)
            result = result.replace("=" * 70, "")

            # Getting Status Code from SDK Output
            search_for_status = re.search("Error\s+(\d\d\d)\s+(.*)",
                                        result)

            if search_for_status is not None:
                status_code = search_for_status.group(1)

            # Getting Result from SDK Output
            search_for_result = re.search(">>[\s\S]*HTTP\s*response\s*text:((?:[\S\s]*\n)+)",
                                        result)
            if search_for_result is not None:
                sdk_result = search_for_result.group(1)
        return status_code, sdk_result

    def isRestSdkInstalled(self, ufm_server):
        chk_file = "%s/%s.pyo" %(Constants.SDK_BASE_DIR, Constants.SYSTEMS_MODULE)
        return self.utils.isFileExist(chk_file)

    def getUfmIP(self):
        ufm_manual_ip = self.utils.read_conf_file(Constants.CONF_UFM_IP)
        if ufm_manual_ip:
            try:
                IP(ufm_manual_ip)
                return ufm_manual_ip, None
            except Exception as ex:
                return None, 'Error in parsing manual UFM IP. ' + str(ex)
class Integration:
    utils=GeneralUtils()
    ufm=UFM()
    def getJobNodesName(self):
        command = "scontrol show hostname $SLURM_JOB_NODELIST"
        _, result, _ = self.utils.run_cmd(command)
        return result

    def getSlurmLogicalServers(self, ufm_server, env_name):
        all_ls = self.ufm.getLogicalServer(ufm_server, env_name)
        slurm_ls_names = [ls['name'] for ls in all_ls if ls['name'].startswith(Constants.LS_JOB_NAME)]
        return slurm_ls_names

    def getRunningSLurmJobsID(self):
        command = """squeue| awk '{if ($5=="R") print $1}'"""
        _, result, _ = self.utils.run_cmd(command)
        jobs = result.splitlines()
        return jobs