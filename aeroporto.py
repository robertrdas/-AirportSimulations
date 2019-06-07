'''
Robert Douglas de A Santos
Anderson Silva Fonseca
Domingos dias
'''
import itertools
import random
from statistica import Estatisticas
import numpy as np
import simpy

RANDOM_SEED = 42
GAS_STATION_SIZE = 5000  # litros do caminhão
FUEL_TANK_SIZE = 16000  # litros maximos
FUEL_TANK_LEVEL = [1445, 9752]  # Min/max litros do avião
REFUELING_SPEED = 5  # litros / segundos
TANK_TRUCK_TIME = 300  # Tempo de chegada do caminhão tanque
T_INTER = [1800, 7200]  # Tempo de criação das aeronaves 30min a 4 horas
SIM_TIME = 86400  # Tempo da simulação em segundos 24 horas
PROB_ABASTECE = 10 # probabilidade de abstecer
TEMPO_PISTA = [1200, 1800] #tempo que ficara na pista
TEMPO_DECOLAGEM = [120, 180] #tempo para decolar
PASSAGEIROS = [86, 220] #numero de passageiros
TEMPO_EMB_DES = [45, 90] #tempo de desembarque
THRESHOLD = 10  # Threshold for calling the tank truck (in %)


def airplane(name, env, pista, finger, passageiros, fuel_tank_level, gas_station, fuel_pump):
  
	global num_avioes
	global tempo_termino
	global numAv_atendidos
	global num_avioes_finger


	print('%s chegou no aeroporto as %1.f'
		  % (name, env.now))

	"""Solicita pista de pouso"""
	with pista.request() as req:
		start = env.now

		yield req
		tempoChegada = env.now

		print('%s esperou %.1f segundos para usar a pista'
			   %(name, env.now))
		num_avioes +=1

		taxiando = random.randint(*TEMPO_PISTA)
		tempo_pista.append(taxiando)
		yield env.timeout(taxiando)

	flag = False

	"""Solicita um finger"""
	with (finger.request()) as req:

		start = env.now

		yield req
		ini_finger = env.now
		num_avioes_finger +=1
		print('%s esperou %1.f segundos para usar um dos fingers' % (name, env.now-start ))

		tempo_emb_des = 0
		"""Desembarcando passageiros"""
		for i in range(passageiros):
			tempo_emb_des += random.randint(*TEMPO_EMB_DES)

		passageiros = random.randint(*PASSAGEIROS)

		"""Embarcando passageiros"""
		for i in range(passageiros):
			tempo_emb_des += random.randint(*TEMPO_EMB_DES)

		yield env.timeout(tempo_emb_des)
		termino_finger = env.now 
		tempo_finger.append(termino_finger - start)
		print('Tempo de embarque/desembarque do aviao {} terminou em {}!'.format(name,env.now));
		i = np.random.random() * PROB_ABASTECE
		flag = True

	if i > 5:
		"""Caso precise abastecer"""
		with gas_station.request() as req:
			start = env.now
			# Request one of the gas pumps
			print('%s foi abastecer  as %1.f'
				  % (name, env.now))
			yield req  # Get the required amount of fuel
			liters_required = FUEL_TANK_SIZE - fuel_tank_level

			yield env.timeout(liters_required)
			print('%s terminou de abastecer as %.1f seconds.' % (name, env.now ))
			with pista.request() as req:
				start = env.now
				print('%s foi para pista de decolagem  as %1.f'
					  % (name, env.now))
				yield req

				taxiando = random.randint(*TEMPO_PISTA)
				tempo_pista.append(taxiando)
				yield env.timeout(taxiando)
				tempoDecolagem = env.now
				tempSolo = tempoDecolagem - tempoChegada
				tempo_solo.append(tempSolo)
				numAv_atendidos +=1
				tempo_termino = tempoDecolagem -start
				print('%s DECOLOU as %.1f seconds e ficou %d no solo' % (name, env.now,tempSolo))
				
		"""Solicita umaa pista para decolar"""
	else:
		with pista.request() as req:
			start = env.now
			print('%s foi para pista de decolagem  as %1.f'
				  % (name, env.now))
			yield req

			taxiando = random.randint(*TEMPO_PISTA)
			tempo_pista.append(taxiando)
			yield env.timeout(taxiando)
			tempoDecolagem = env.now
			tempSolo = tempoDecolagem - tempoChegada
			tempo_solo.append(tempSolo)
			numAv_atendidos +=1
			tempo_termino = tempoDecolagem - start
			print('%s DECOLOU as %.1f seconds e ficou %d no solo' % (name, env.now,tempSolo))

def gas_station_control(env, fuel_pump):

	while True:
		if fuel_pump.level / fuel_pump.capacity * 100 < THRESHOLD:
			# We need to call the tank truck now!
			print('Chamando o caminhão tanque %d' % env.now)
			# Wait for the tank truck to arrive and refuel the station
			yield env.process(tank_truck(env, fuel_pump))

		yield env.timeout(10)  # Check every 10 seconds


def tank_truck(env, fuel_pump):
	"""
	Chegado docaminhão tanque depois de um certo atraso
	e o processo de reabastecimento 
	"""
	yield env.timeout(TANK_TRUCK_TIME)
	print('Caminhão tanque chegou em: %d' % env.now)
	ammount = fuel_pump.capacity - fuel_pump.level
	print('Caminhão tanque reabasteceu %.1f litros.' % ammount)
	yield fuel_pump.put(ammount)


def airplane_generator(env, pista, finger, gas_station, fuel_pump):
	"""
	Gera um novo avião
	Com o numero de passageiros no intervalo definido
	Com combustivel no tanque dentro do intervalo definido
	"""
	for i in itertools.count():
		yield env.timeout(random.randint(*T_INTER))
		passageiros = random.randint(*PASSAGEIROS)
		fuel_tank_level = random.randint(*FUEL_TANK_LEVEL)
		env.process(airplane('Aviao %d' % i, env, pista, finger, passageiros, fuel_tank_level, gas_station, fuel_pump))


# Setup and start the simulation
print('Aeroporto')

#ainda n tem nada de util na classe estatistica
results = list()
for i in range(5):
	num_avioes = 0
	num_avioes_finger = 0
	numAv_atendidos = 0 # ou seja, pousa e decola. A simulação pode acabar antes q todos os aviões decolem
	tempo_solo= list()
	tempo_finger = list()
	tempoChegada = 0
	tempoDecolagem = 0
	tempo_pista = list()
	tempo_termino = 0 # tempo de execução até ultimo que decolou
	random.seed(RANDOM_SEED)

	# Create environment and start processes
	env = simpy.Environment()
	gas_station = simpy.Resource(env, 1)
	pista = simpy.Resource(env, 2)
	finger = simpy.Resource(env,4)
	fuel_pump = simpy.Container(env, GAS_STATION_SIZE, init=GAS_STATION_SIZE)
	env.process(gas_station_control(env, fuel_pump))
	env.process(airplane_generator(env, pista, finger, gas_station, fuel_pump))

	# Execute!
	env.run(until=SIM_TIME)

	est = Estatisticas.Estatistica(num_avioes, tempo_solo, tempo_termino , numAv_atendidos , tempo_finger, num_avioes_finger)
	#print("Tempo medio no solo :",est.temp_med_solo()/3600)
	#numAtendidos = est.num_av_atendidos()
	#print("Numero de aeronaves atendidas por hora: ",numAtendidos)
	#print("Fingers: ",est.uti_finger()/3600)
	#print("Tempo de pista: ",est.uti_pista(tempo_pista)/3600)
	print(est.uti_pista(tempo_pista)/SIM_TIME)
	results.append((round(est.temp_med_solo()/3600,2),round(est.num_av_atendidos(),2),round(est.uti_finger()/3600,2),round(est.uti_pista(tempo_pista)/3600,2)))

tempo_medio_solo = 0;
numero_medio_avioes = 0;
tempo_medio_fingers = 0;
tempo_medio_pista = 0;

for i in results:
	print(i)
for i in range(len(results)):
	tempo_medio_solo += results[i][0];
	numero_medio_avioes += results[i][1];
	tempo_medio_fingers += results[i][2];
	tempo_medio_pista += results[i][3];

print(str(round(tempo_medio_solo/5,2)).replace('.',','))
print(str(round(numero_medio_avioes/5,2)).replace('.',','))
print(str(round(tempo_medio_fingers/5,2)).replace('.',','))
print(str(round(tempo_medio_pista/5,2)).replace('.',','))