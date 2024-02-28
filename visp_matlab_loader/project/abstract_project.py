from abc import ABC, abstractmethod

from visp_matlab_loader.execute.abstract_executor import AbstractExecutor




class AbstractProject(ABC):
    @abstractmethod
    def executor(self) -> AbstractExecutor:
        pass

    @property
    @abstractmethod
    def name(self):
        pass
