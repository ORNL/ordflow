from enum import Enum
import os
from sys import platform
from warnings import warn
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
                   "Authorization": self._API_KEY}
        response = requests.get(url, headers=headers)
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
                         "Authorization": self._API_KEY}
        basic_headers.update(headers)
        response = requests.post(url,
                                 headers=basic_headers,
                                 json=json, files=files,
                                 data=data)
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

    def endpoints_active(self):
        """
        Checks whether both source and destination Globus endpoints are active

        Returns
        -------
        dict
            Response from GET request
        """
        url = "%s/%s" % (self._API_URL, 'endpoints/activation')
        # TODO: What should this response look like to be pythonic?
        return self.__get(url)

    def endpoints_activate(self, username, password, endpoint="destination"):
        """

        Parameters
        ----------
        username : str
            user name
        password : str
            password
        endpoint : str, Optional
            Which endpoint to activate. Currently "source" and "destination"
            are the only values accepted

        Returns
        -------
        dict
            Response from GET request
        """
        path = 'endpoints/activate?endpoint={}&username={}&password={}'.format(endpoint, username, password)
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
            Scientific metadata associated with this dataset

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
        # TODO: Use metadata!

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
        NOTE - this method does NOT yet work

        Parameters
        ----------
        file_path : str
            Local path to file that needs to be uploaded
        dataset_id : int
            Dataset ID to upload this file to
        relative_path : str, optional
            Relative path in destination to place this file.
            Default - the file will be uploaded to the root directory of the dataset
        transport : dflow.Transport, optional
            Transport protocol to use to transfer this specific file

        Returns
        -------
        dict
            Response from POST request
        """
        path = 'dataset-file-upload'
        url = "%s/%s" % (self._API_URL, path)

        self.__validate_integer(dataset_id, "dataset_id", min_val=0)

        file_handle = open(file_path, "rb")

        form_data = {'dataset_id': dataset_id,
                     'transport': 'globus'}

        if relative_path:
            if not isinstance(relative_path, str):
                raise TypeError("relative_path should be a string")
            form_data.update({'relative_path': relative_path})

        if not transport:
            print("using Globus since other file transfer adapters have not been implemented")

        response = self.__post(url,
                               files={'file': file_handle},
                               data=form_data)

        file_handle.close()

        return response

    def file_upload_curl(self, file_path, dataset_id, relative_path=None, transport=None, verbose=True):
        """
        Upload the provided file to the specified Dataset

        Parameters
        ----------
        file_path : str
            Local path to file that needs to be uploaded
        dataset_id : int
            Dataset ID to upload this file to
        relative_path : str, optional
            Relative path in destination to place this file.
            Default - the file will be uploaded to the root directory of the dataset
        transport : dflow.Transport, optional
            Transport protocol to use to transfer this specific file
        verbose : bool, optional
            Whether or not to print out the curl command that will be sent out on shell
            for debugging and validation purposes.
            Default = True

        Returns
        -------
        int
            return value from os.system
        """
        warn("The behavior and output of this function are expected to change"
             "significantly in the future. "
             "The inputs are expected to be the same, however", FutureWarning)
        self.__validate_str_parm(file_path, "file_path")
        if not os.path.exists(file_path):
            raise FileNotFoundError("{} not found".format(file_path))

        self.__validate_integer(dataset_id, "dataset_id", min_val=0)

        if transport:
            if not isinstance(transport, Transport):
                raise TypeError("transport should be of type dflow.Transport")

        path = 'dataset-file-upload'
        url = "%s/%s" % (self._API_URL, path)

        cmd = ["curl -X 'POST'",
               "'{}'".format(url),
               "-H 'accept: */*'",
               "-H 'Content-Type: multipart/form-data'",
               "-H 'Authorization: {}'".format(self._API_KEY),
               "-F 'file=@{}'".format(file_path),
               "-F 'dataset_id={}'".format(dataset_id),
               ]
        if relative_path:
            cmd.append("-F 'relative_path={}'".format(relative_path))

        if not transport:
            print("using Globus since others have not been implemented")

        cmd.append("-F 'transport=globus'")

        if verbose:
            print('curl command that will be called:')
            print(' \\ \n'.join(cmd))

        if platform == "win32":
            warn("Currently building and executing curl command. "
                 "This may not work on Windows", RuntimeWarning)
        return os.system(' '.join(cmd))
