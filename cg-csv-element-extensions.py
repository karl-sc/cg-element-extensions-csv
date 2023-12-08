#!/usr/bin/env python3
PROGRAM_NAME = "cg-csv-element-extensions.py"
PROGRAM_DESCRIPTION = """
CloudGenix script
---------------------------------------

"""
from cloudgenix import API, jd
import os
import sys
import argparse
import csv

CLIARGS = {}
cgx_session = API()              #Instantiate a new CG API Session for AUTH

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=PROGRAM_DESCRIPTION
            )
    parser.add_argument('--token', '-t', metavar='"MYTOKEN"', type=str, 
                    help='specify an authtoken to use for CloudGenix authentication')
    parser.add_argument('--authtokenfile', '-f', metavar='"MYTOKENFILE.TXT"', type=str, 
                    help='a file containing the authtoken')
    parser.add_argument('--csvfile', '-c', metavar='csvfile', type=str, 
                    help='the CSV Filename to write', default="site-extension-list.csv", required=False)
    parser.add_argument('--namespace', '-n', metavar='csvfile', type=str, 
                    help='the Namespace to look for', default='thresholds/lqm/app', required=False)
    args = parser.parse_args()
    CLIARGS.update(vars(args)) ##ASSIGN ARGUMENTS to our DICT
    print(CLIARGS)

def authenticate():
    print("AUTHENTICATING...")
    user_email = None
    user_password = None
    
    ##First attempt to use an AuthTOKEN if defined
    if CLIARGS['token']:                    #Check if AuthToken is in the CLI ARG
        CLOUDGENIX_AUTH_TOKEN = CLIARGS['token']
        print("    ","Authenticating using Auth-Token in from CLI ARGS")
    elif CLIARGS['authtokenfile']:          #Next: Check if an AuthToken file is used
        tokenfile = open(CLIARGS['authtokenfile'])
        CLOUDGENIX_AUTH_TOKEN = tokenfile.read().strip()
        print("    ","Authenticating using Auth-token from file",CLIARGS['authtokenfile'])
    elif "X_AUTH_TOKEN" in os.environ:              #Next: Check if an AuthToken is defined in the OS as X_AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
        print("    ","Authenticating using environment variable X_AUTH_TOKEN")
    elif "AUTH_TOKEN" in os.environ:                #Next: Check if an AuthToken is defined in the OS as AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        print("    ","Authenticating using environment variable AUTH_TOKEN")
    else:                                           #Next: If we are not using an AUTH TOKEN, set it to NULL        
        CLOUDGENIX_AUTH_TOKEN = None
        print("    ","Authenticating using interactive login")
    ##ATTEMPT AUTHENTICATION
    if CLOUDGENIX_AUTH_TOKEN:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("    ","ERROR: AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None            
    print("    ","SUCCESS: Authentication Complete")

#| write_2d_list_to_csv - Writes a 2-Dimensional list to a CSV file
def write_2d_list_to_csv(csv_file, list_2d, write_mode="w"):
    import csv
    try:
        file = open(csv_file, write_mode)
        with file:    
            write = csv.writer(file)
            write.writerows(list_2d)
            return True
        return False
    except:
        return False


def go():
    ####CODE GOES BELOW HERE#########
    resp = cgx_session.get.tenants()
    if resp.cgx_status:
        tenant_name = resp.cgx_content.get("name", None)
        print("======== TENANT NAME",tenant_name,"========")
    else:
        logout()
        print("ERROR: API Call failure when enumerating TENANT Name! Exiting!")
        print(resp.cgx_status)
        sys.exit((vars(resp)))

    csvfilename = CLIARGS['csvfile']
    
    csv_out_array = []
    site_id_name_mapping = {}
    namespace = CLIARGS['namespace']
    print("Searching through all elements for Extension entries with NameSpace",namespace)
    
    # get SITE_ID to friendly site name mapping so the CSV is more readable
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        site_list = resp.cgx_content.get("items", None)
        for site in site_list:        
            site_id_name_mapping[site['id']] = site['name']
    else:
        logout()
        print("ERROR: API Call failure when enumerating SITES in tenant! Exiting!")
        sys.exit((jd(resp)))
    
    counter = 0

    #begin iterating through all elements to build our CSV File
    element_list = cgx_session.get.elements().cgx_content.get("items", None)
    
    # CSV Columns should be [ SiteName, ElementID, ElementName, Namespace_name, Namespace_count, Namespace_data ]
    csv_out_array.append( ["Site_Name", "Element_ID", "Element_Name", "Namespace", "Num_of_Entries", "Extension_Data"])
    master_list_of_results = []
    extension_type_counts = {}
    counter = 0
    for element in element_list:
        counter = counter + 1
        site_id = element['site_id']
        element_id = element['id']
        element_name = element['name']
        result = cgx_session.get.element_extensions(site_id,element_id)
        element_namespace_data = ""
        element_namespace_count = 0
        for extension in result.cgx_content.get("items",[]):
            if (extension.get('namespace',None) == namespace):
                entity_id = extension.get('entity_id',None)
                entity_conf = extension.get('conf',None)
                element_namespace_count = element_namespace_count + 1
                element_namespace_data = element_namespace_data + "{ entity_id:" + str(entity_id) + "," + str(entity_conf) + " }"
        ### Append per Element Extensions found to CSV
        csv_out_array.append([
            site_id_name_mapping[site_id],
            element_id,
            element_name,
            namespace,
            element_namespace_count,
            element_namespace_data,
                            ])
    result = write_2d_list_to_csv(csvfilename, csv_out_array)
    if result:
        print("Wrote to CSV File:", csvfilename, " - ", counter, 'rows')
    else:
        print("Error Writing to CSV File:", csvfilename, " - ", counter, 'rows')
    ####CODE GOES ABOVE HERE#########
  
def logout():
    print("Logging out")
    cgx_session.get.logout()

if __name__ == "__main__":
    parse_arguments()
    authenticate()
    go()
    logout()
