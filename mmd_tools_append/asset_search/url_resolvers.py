# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

from abc import ABC, abstractmethod

import requests

from .actions import DownloadActionExecutor


class URLResolverABC(ABC):
    @abstractmethod
    def resolve(self, url: str) -> requests.models.Response:
        pass


class URLResolver(URLResolverABC):
    def resolve(self, url: str) -> requests.models.Response:
        if url.startswith("http://") or url.startswith("https://"):
            return requests.get(url, stream=True)
        return DownloadActionExecutor.execute_action(url)
