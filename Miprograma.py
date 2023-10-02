#Importar la interfz de un archivo externo
import typing
from PyQt5 import QtCore,QtWidgets, QtGui
from PyQt5.QtWidgets import QWidget
from newmain import *

#Importar las librerias para el funcionamiento de la aplicaci[on en segundo plano
from PyQt5.QtCore import pyqtSlot,QThreadPool,QRunnable,pyqtSignal,QObject, Qt

#Importacion de la librerias para el I/O de la rasperry
from time import sleep
from pyA20.gpio import gpio
from pyA20.gpio import port

#Importamos las librerias para los sensores de temperatura 1-W
#Libreria para los sensores DS18b20
from w1thermsensor import W1ThermSensor   #Sensores 1-W pin7 del Orange pi
#Libreria para el sensor DHT11
import dht   #Sensor DHT11 pin seleccionable

#Se declara el I/O
gpio.init()   #Se inicializa el I/O de la Orange pi (Nota: para correr el programa con esta parte se tiene que correr como administrador "sudo python3 Miprograma.py")
S=port.PA14   #Pin del sensor DHT11
#El pin del sensor DS18b20 se declara en archivos externos, vea el archivo "Orange pi pc" en el drive, en la seccion correspondiente a este tema.

#Clase para declarar las señales que se estaran pasando de Worker(segundo plano) a la interfaz(primer plano)
class Signals(QObject):
    V_lbltemperatura = pyqtSignal(int)
    V_lblhumedad = pyqtSignal(int)
    TempAF = pyqtSignal(int)
    TempAC = pyqtSignal(int)
    Estado = pyqtSignal(int)
    
class Worker(QRunnable): 
	def __init__(self):
		super(Worker, self).__init__() 
		self.signals = Signals()
		
	#@pyqtSlot()
	def run(self):
		
		Tsensors=[]
		IdTsensors=[]

		DHT11_instance = dht.DHT11(pin=S)
		
		while True:
			Temps=[]
			
			DHT11_result = DHT11_instance.read()
			
			if DHT11_result.is_valid():
				T=DHT11_result.temperature
				H=DHT11_result.humidity
				self.signals.V_lbltemperatura.emit(T)
				self.signals.V_lblhumedad.emit(H)				
			
			Tsensors = W1ThermSensor.get_available_sensors()
	
			if len(Tsensors) != 0:
				if len(Tsensors) < 1:
					print("Problema: detectado menos de 4 sensores")
				else:
					for m in range(len(Tsensors)):
						IdTsensors.append(Tsensors[m].id)
			else:
				print("sin sensores")
			
			
			for m in range(len(Tsensors)):
				try:
					Temps.append([Tsensors[m].id, Tsensors[m].get_temperature()])
					if Temps[m][0] == "3c01f096f7de" :   #Sensor de temperatura del Compresor
						self.signals.TempAF.emit(Temps[m][1])
						if Temps[m][1] > 60:#60   #Punto de sobrecalentamiento. ###Que pase sobre los 60grados
							self.signals.Estado.emit(1)
						sleep(2)
						
					if Temps[m][0] == "3c01f096496e" :   #Sensor de temperatura del Espiral
						self.signals.TempAC.emit(Temps[m][1])
						if Temps[m][1] < 0:#0   #Punto de congelamiento de la espeiral ###Que pase debajo de los 0grados
							self.signals.Estado.emit(2) 
						sleep(2)
						
					'''	### Temperaturas de los tanques de agua ###
					#Depende del tipo de maquina hay que activar estas temperaturas
					if if Temps[m][0] == "3c01f096496e" :  #Sensor de temperatura agua fria ###Cambiar ID de sensor por el correspondiente
						self.signals.TempAC.emit(Temps[m][1])
						
					if Temps[m][0] == "3c01f096496e" :   #Sensor de temperatura agua caliente ###Cambiar ID de sensor por el correspondiente
						self.signals.TempAC.emit(Temps[m][1])
					'''
					
				except:
					self.signals.V_lbltemperatura.emit(0)
					print("Mala lectura " + str(m))

			#sleep(2)
    
		
			
class VentanaPrincipal(QtWidgets.QMainWindow, Ui_MainWindow):  #Ventana principal
	def __init__(self):
		super(VentanaPrincipal, self).__init__()
		self.setupUi(self)
       
		self.threadpool = QThreadPool()
        
		worker = Worker()
		worker.signals.V_lbltemperatura.connect(lambda temperatura: self.V_lbltemperatura.setText(str(temperatura)))
		worker.signals.V_lblhumedad.connect(lambda humedad: self.V_lblhumedad.setText(str(humedad)))
		worker.signals.TempAF.connect(lambda TAF: self.V_lblfiltros.setText("Agua F: " + str(TAF)))
		worker.signals.TempAC.connect(lambda TAC: self.V_lblfiltros.setText("Agua C: " + str(TAC)))
		worker.signals.Estado.connect(self.Estado)
		self.threadpool.start(worker)
        
	def Estado(self,a):
		if a == 1:
			self.movie.setPaused(True)
			self.V_lblestados.setText("Calentamiento")
			self.V_lblestados.setStyleSheet("background-color: red")
			
		if a== 2:
			self.movie.setPaused(True)
			self.V_lblestados.setText("Congelamiento")
			self.V_lblestados.setStyleSheet("background-color: red")
		 

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = VentanaPrincipal()
    window.show()
    app.exec_()
