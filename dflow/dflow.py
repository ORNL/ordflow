from enum import Enum
import os
import requests


class Transport(Enum):
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
                                 json=json, files=files)
        return response.json()

    @staticmethod
    def __validate_dset_id(dataset_id):
        """
        Validates dataset ID

        Parameters
        ----------
        dataset_id : int
            ID for dataset

        Returns
        -------
        None

        Raises
        ------
        TypeError
        ValueError
        """
        if not isinstance(dataset_id, int):
            raise TypeError("dataset_id should be an integer > 0")
        if dataset_id < 0:
            raise ValueError("dataset_id should be > 0")

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
        path = 'datasets/search?q={}'.format("blah")
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def dataset_info(self, dset_id):
        if not isinstance(dset_id, int):
            raise TypeError("dset_id should be a positive integer")
        elif dset_id < 0:
            raise ValueError("dset_id should be a positive integer")
        path = 'datasets/{}'.format(dset_id)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def dataset_create(self, title, instrument_id=0, metadata=None):
        url = "%s/%s" % (self._API_URL, "datasets")
        data = {"name": title,
                "instrument_id": instrument_id}
        # TODO: Use metadata!

        return self.__post(url,
                           headers={"Content-Type": "application/json"},
                           json=data)

    def files_search(self, query, dataset_id=None):
        path = 'dataset-files/search?q={}'.format(query)
        if dataset_id is not None:
            self.__validate_dset_id(dataset_id)
            path += "&dataset_id={}".format(dataset_id)
        url = "%s/%s" % (self._API_URL, path)
        return self.__get(url)

    def file_upload(self, file_path, dataset_id, relative_path=None, transport=None):
        path = 'dataset-file-upload'
        url = "%s/%s" % (self._API_URL, path)

        self.__validate_dset_id(dataset_id)

        file_handle = open(file_path, "rb")

        files = {'file': file_handle,
                 'dataset_id': dataset_id,
                 'transport': 'globus'}

        if relative_path:
            if not isinstance(relative_path, str):
                raise TypeError("relative_path should be a string")
            files.update({'relative_path': relative_path})

        if not transport:
            print("using Globus since others have not been implemented")

        headers = {"Content-Type": "multipart/form-data"}

        response = self.__post(url, files=files, headers=headers)

        file_handle.close()

        return response

    def file_upload_curl(self, file_path, dataset_id, relative_path=None, transport=None, verbose=True):
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
            print(' \ \n'.join(cmd))

        os.system(' '.join(cmd))
