 from abc import ABC,abstractmethod

 class components(ABC):
     @abstractmethod
     def button(self):
         pass

     @abstractmethod
     def textfiled(self):
         pass

     @abstractmethod
     def checkbox(self):
         pass

 class component(components):
     def button(self, message: str):
         self.color = message
         return self.color

     def textfield(self, message: int):
         self.size = message
         return self.size

     def checkbox(self, message: int):
         self.nr = message
         return self.nr

 class factory(ABC):
     @abstractmethod
     def create_by_theme(self):
         pass

class darkFactory(factory):
    def create_by_theme(self):
        return component()

class lightFactory(factory):
    def create_by_theme(self):
        return component()