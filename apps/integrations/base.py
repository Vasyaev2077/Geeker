from abc import ABC, abstractmethod


class BaseStorageAdapter(ABC):
    @abstractmethod
    def upload_file(self, file, path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: str) -> None:
        raise NotImplementedError


class BaseEmailAdapter(ABC):
    @abstractmethod
    def send_mail(self, subject: str, body: str, to: list[str]) -> None:
        raise NotImplementedError








