from enum import Enum
from collections.abc import MutableMapping
import os
import requests


class Transport(Enum):
    """
    The different data transfer protocols supported by DataFlow
    """
    GLOBUS = 0
    HTTPS = 1


class API(object):

    def __init__(self, api_key, server_url=None):
        """
        Creates an instance of the API class to communicate with DataFlow

        Parameters
        ----------
        api_key : str
            API key for accessing DataFlow
        server_url : str, Optional
            URL for DataFlow server.
            Default: staging server
        """
        if not isinstance(api_key, str):
            raise TypeError("api_key should be a string. Generate this from DataFlow")
        if server_url:
            if not isinstance(server_url, str):
                raise TypeError("server_url should be a str")
            self._API_URL = server_url
        else:
            print("Using staging server as default")
            self._API_URL = "https://dataflow-staging.ornl.gov/api/v1"
        self._API_KEY = api_key

    def __get(self, url):
        """
        Internal function to send GET requests

        Parameters
        ----------
        url : str
            URL for GET request

        Returns
        -------
        dict
            Response to GET request
        """
        headers = {"accept": "*/*",
                   "Authorization": "Bearer " + self._API_KEY}
        response = requests.get(url, headers=headers)
        if not response.ok:
            raise ValueError("{}: {}".format(response.reason, response.text[1:-1]))
        return response.json()

    def __post(self, url, headers={}, json=None, data=None, files=None):
        """

        Parameters
        ----------
        url : str
            URL for POST request
        headers : dict, optional
            Headers besides the accept and auth token
        json : dict, optional
            Dict
        data : dict, optional
            Key-value pairs for the form
        files : dict
            Dict

        Returns
        -------
        dict
            Response to POST request
        """
        # TODO: Use **kwargs instead
        basic_headers = {"accept": "*/*",
                         "Authorization": "Bearer " + self._API_KEY}
        basic_headers.update(headers)
        response = requests.post(url,
                                 headers=basic_headers,
                                 json=json, files=files,
                                 data=data)
        if not response.ok:
            raise ValueError("{}: {}".format(response.reason, response.text[1:-1]))
        return response.json()

    @staticmethod
    def __validate_integer(value, title, min_val=0):
        """
        Validates integer parameter

        Parameters
        ----------
        value : int
            value to validate

        Returns
        -------
        None

        Raises
        ------
        TypeError
        ValueError
        """
        if not isinstance(value, int):
            raise TypeError("{} should be an int".format(title))
        if value < min_val:
            raise ValueError("{} should be > {}".format(title, min_val))

    @staticmethod
    def __validate_str_parm(value, title):
        """
        Validate string parameter

        Parameters
        ----------
        value : str
            Object to test
        title : str
            Name of variable or parameter

        Returns
        -------
        None

        Raises
        ------
        TypeError
        ValueError
        """
        mesg = '{} should be a non empty string'.format(title)
        if not isinstance(value, str):
            raise TypeError(mesg)
        title = title.strip()
        if len(title) < 1:
            raise ValueError(mesg)

    @staticmethod
    def __flatten_dict(nested_dict, separator='-'):
        """
        Flattens a nested dictionary
        Parameters
        ----------
        nested_dict : dict
            Nested dictionary
        separator : str, Optional. Default='-'
            Separator between the keys of different levels
        Returns
        -------
        dict
            Dictionary whose keys are flattened to a single level
        Notes
        -----
        Taken from https://stackoverflow.com/questions/6027558/flatten-nested-
        dictionaries-compressing-keys
        """
        if not isinstance(nested_dict, dict):
            raise TypeError('nested_dict should be a dict')

        def __flatten_dict_int(nest_dict, sep, parent_key=''):
            items = []
            if sep == '_':
                repl = '-'
            else:
                repl = '_'
            for key, value in nest_dict.items():
                if not isinstance(key, str):
                    key = str(key)
                if sep in key:
                    key = key.replace(sep, repl)

                new_key = parent_key + sep + key if parent_key else key
                if isinstance(value, MutableMapping):
                    items.extend(__flatten_dict_int(value, sep, parent_key=new_key).items())
                # nion files contain lists of dictionaries, oops
                elif isinstance(value, list):
                    for i in range(len(value)):
                        if isinstance(value[i], dict):
                            for kk in value[i]:
                                items.append(('dim-' + kk + '-' + str(i), value[i][kk]))
                        else:
                            if type(value) != bytes:
                                items.append((new_key, value))
                else:
                    if type(value) != bytes:
                        items.append((new_key, value))
            return dict(items)

        return __flatten_dict_int(nested_dict, separator)

    def settings_get(self):
        """
        Gets current default user settings

        Returns
        -------
        dict
            Response from GET request
        """
        path = "user-settings"
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def settings_set(self, setting, value):
        """
        Set or update default user settings

        Parameters
        ----------
        setting : str
            Name of parameter
            Currently, only "globus.destination_endpoint" and "transport.protocol" are supported
        value : obj
            New value for chosen parameter

        Returns
        -------
        dict
            Response from POST request
        """
        self.__validate_str_parm(setting, "setting")
        path = "user-settings/?setting={}&value={}".format(setting, value)
        url = "%s/%s" % (self._API_URL, path)
        return self.__post(url)

    def instrument_list(self):
        """
        List all instruments connected to this DataFlow server

        Returns
        -------
        dict
            Response from GET request
        """
        url = "%s/%s" % (self._API_URL, "instruments")
        return self.__get(url)

    def instrument_info(self, instr_id):
        """
        Show information about an Instrument

        Parameters
        ----------
        instr_id : int
            ID for Insrtument

        Returns
        -------
        dict
            Response from GET request
        """
        self.__validate_integer(instr_id, "instr_id", min_val=0)
        path = 'instruments/{}'.format(instr_id)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def globus_endpoints_active(self, endpoint=None):
        """
        Checks whether both source and destination Globus endpoints are active

        Parameters
        ----------
        endpoint : str, Optional. 
            UUID of endpoint whose status needs to be checked. 
            Default = None - checks the default destination Globus endpoint 
            along with the DataFlow server's endpoint

        Returns
        -------
        dict
            Response from GET request
        """
        url = "%s/%s" % (self._API_URL, 'transports/globus/activation')
        if isinstance(endpoint, str):
            url += "?endpoint=" + endpoint
        # TODO: What should this response look like to be pythonic?
        return self.__get(url)

    def globus_endpoints_activate(self, username, password, encrypted=True, endpoint="destination"):
        """
        Activates Globus endpoints necessary to transfer data

        Parameters
        ----------
        username : str
            user name
        password : str
            password
        encrypted : bool, Optional
            Whether or not the password is encrypted (using the DataFlow web server's encryption).
            Default = encrypted password
        endpoint : str, Optional
            Endpoint to activate. 
            The 3 valid options are:
            1. "source" - DataFlow server's endpoint, 
            2. "destination" - Where data will be sent to, 
            and 3. the UUID of some other endpoint

        Returns
        -------
        dict
            Response from GET request
        """
        pwd_prefix = "encrypted"
        if not encrypted:
            pwd_prefix = "unencrypted"
        path = 'transports/globus/activate?endpoint={}&username={}&{}_password={}'.format(endpoint, username,
                                                                                          pwd_prefix, password)
        url = "%s/%s" % (self._API_URL, path)
        return self.__post(url)

    def dataset_search(self, query):
        """
        Search for a dataset in DataFlow

        Parameters
        ----------
        query : str
            Text or date to search on

        Returns
        -------
        dict
            Response from GET request
        """
        self.__validate_str_parm(query, "query")
        # TODO: Verify that spaces and other non alphanumeric characters are correctly encoded
        path = 'datasets/search?q={}'.format(query)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def dataset_info(self, dset_id):
        """
        Show information about a dataset

        Parameters
        ----------
        dset_id : int
            ID for dataset

        Returns
        -------
        dict
            Response from GET request
        """
        self.__validate_integer(dset_id, "dset_id", min_val=0)
        path = 'datasets/{}'.format(dset_id)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    @staticmethod
    def __mdata_dict_2_list(metadata):
        """
        Converts metadata dictionary to a list amenable to DataFlow

        Parameters
        ----------
        metadata: dict
            Metadata specified as {key_1: value_1, key_2: value_2}

        Returns
        -------
        list
            Metadata reformatted as:
            [{"field_name": key_1, "field_value": value_1}, 
             {"field_name": key_2, "field_value": value_2}]
        """
        mdlist = list()
        for key, val in metadata.items():
            mdlist.append({"field_name": key, "field_value": val})
        return mdlist

    def dataset_create(self, title, instrument_id=0, metadata=None):
        """
        Create a new dataset

        Parameters
        ----------
        title : str
            Title for dataset
        instrument_id : int, optional
            Instrument ID. Default = 0 - UnknownInstrument
        metadata : dict, optional
            Scientific metadata associated with this dataset.
            Metadata specified as {"param 1": value_1, "param 2": value_2}
            Nested dictionaries will be flattened with keys joined with a "-" separator

        Returns
        -------
        dict
            Response from POST request
        """
        self.__validate_str_parm(title, "title")
        if metadata:
            if not isinstance(metadata, dict):
                raise TypeError("metadata should be a dict")

        url = "%s/%s" % (self._API_URL, "datasets")
        data = {"name": title,
                "instrument_id": instrument_id}
        if isinstance(metadata, dict):
            flat_md = self.__flatten_dict(metadata)
            mdata_list = self.__mdata_dict_2_list(flat_md)
            data["metadata_field_values_attributes"] = mdata_list

        return self.__post(url,
                           headers={"Content-Type": "application/json"},
                           json=data)

    def files_search(self, query, dataset_id=None):
        """
        Search for individual files in datasets

        Parameters
        ----------
        query : str
            Search query
        dataset_id : int, optional
            Filter results to the specified Dataset. Default - no filtering

        Returns
        -------
        dict
            Response from GET request
        """
        path = 'dataset-files/search?q={}'.format(query)
        if dataset_id is not None:
            self.__validate_integer(dataset_id, "dataset_id", min_val=0)
            path += "&dataset_id={}".format(dataset_id)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def file_upload(self, file_path, dataset_id, relative_path=None, transport=None):
        """
        Upload the provided file to the specified Dataset.

        Parameters
        ----------
        file_path : str
            Local path to file that needs to be uploaded
        dataset_id : int
            Dataset ID to upload this file to
        relative_path : str, optional
            Relative path in destination to place this file.
            Default - the file will be uploaded to the root directory of the dataset
        transport : ordflow.Transport, optional
            Transport protocol to use to transfer this specific file

        Returns
        -------
        dict
            Response from POST request
        """
        path = 'dataset-file-upload'
        url = "%s/%s" % (self._API_URL, path)

        self.__validate_str_parm(file_path, "file_path")
        if not os.path.exists(file_path):
            raise FileNotFoundError("{} not found".format(file_path))

        self.__validate_integer(dataset_id, "dataset_id", min_val=0)

        if transport:
            if not isinstance(transport, Transport):
                raise TypeError("transport should be of type ordflow.Transport")

        file_handle = open(file_path, "rb")

        form_data = {'dataset_id': dataset_id,
                     'transport': 'globus'}

        if relative_path:
            if not isinstance(relative_path, str):
                raise TypeError("relative_path should be a string")
            form_data.update({'relative_path': relative_path})

        if transport != Transport.GLOBUS:
            print("using Globus since other file transfer adapters have not been implemented")

        response = self.__post(url,
                               files={'file': file_handle},
                               data=form_data)

        file_handle.close()

        return response
