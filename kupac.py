import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from slika import Slika
from random import randrange
from spade.message import Message
import json
import time

class Kupac(Agent):
    def __init__(self, jid, password, naziv, aukcioner, kupac_protivnik, budzet, limit): 
        super().__init__(jid, password)
        self.naziv = naziv
        self.aukcioner = aukcioner
        self.kupac_protivnik = kupac_protivnik
        self.budzet = budzet
        self.trenutna_cijena = 0
        self.trenutna_ponuda = None
        self.limit = limit
        self.kupljene_slike = []

    class KupacPonasanje(FSMBehaviour):
        async def on_start(self):
            print(f"Pokrecem kupca: {self.agent.naziv}")

        async def on_end(self):
            print(f"Zavrsavam s kupcem: {self.agent.naziv}")
        
    async def setup(self):
        fsm = self.KupacPonasanje()
        fsm.add_state(name="CekanjeNaPonudu", state=self.CekanjeNaPonudu(), initial=True)
        fsm.add_state(name="SlanjePonude", state=self.SlanjePonude())
        fsm.add_transition(source="CekanjeNaPonudu", dest= "SlanjePonude")
        fsm.add_transition(source="SlanjePonude", dest="CekanjeNaPonudu")
        fsm.add_transition(source="CekanjeNaPonudu", dest="CekanjeNaPonudu")
        self.add_behaviour(fsm)

    class CekanjeNaPonudu(State):
        async def run(self):
            time.sleep(1)
            msg = await self.receive(timeout=5)
            if msg is None:
                print(f"{self.agent.naziv}: Ponuda nije došla.")
                self.set_next_state("CekanjeNaPonudu")
            else:
                ponuda = json.loads(msg.body)
                self.agent.trenutna_ponuda = ponuda
                if 'gotovo' in ponuda:
                    print(f'{self.agent.naziv}: Izvještaj o kupljenim slikama:')
                    for slika in self.agent.kupljene_slike:
                        print(f'{self.agent.naziv}: Naziv: {slika.naziv_slike}, Autor: {slika.naziv_autora}, Kupljeno po cijeni: {slika.cijena}')
                    print("---------------------------------------------------------")
                    await self.agent.stop()
                    return
                if ponuda['prihvaceno']:
                    self.agent.trenutna_cijena = ponuda['cijena']
                    self.set_next_state("SlanjePonude")
                else:
                    self.agent.budzet -= ponuda['cijena']
                    print(f"{self.agent.naziv}: Protivnik je odbio ponudu. Pobjedio sam i kupio sliku: {ponuda['naziv_slike']} za {ponuda['cijena']}")
                    print(f"{self.agent.naziv}: Trenutni budzet: {self.agent.budzet}")
                    print("--------------------------------------------------------- \n")
                    kupljena_slika = Slika(ponuda['cijena'], ponuda['naziv_slike'], ponuda['naziv_autora'])
                    self.agent.kupljene_slike.append(kupljena_slika)
                    
                    msg = Message(to=self.agent.aukcioner,body=json.dumps({'spremno': True}),metadata={"ontology":"aukcija"})
                    await self.send(msg)
                    self.set_next_state("CekanjeNaPonudu")

    class SlanjePonude(State):
        async def run(self):
            self.agent.trenutna_cijena += 50
            if self.agent.trenutna_cijena > self.agent.limit or self.agent.trenutna_cijena > self.agent.budzet:
                self.agent.trenutna_ponuda['prihvaceno'] = False
                msg = Message(to=self.agent.aukcioner,body=json.dumps(self.agent.trenutna_ponuda),metadata={"ontology":"aukcija"})
                print(f"{self.agent.naziv}: Saljem poruku aukcioneru da NE prihvacam ponudu sa cijenom:", self.agent.trenutna_cijena)
                print(f"{self.agent.naziv}: Trenutni budzet: {self.agent.budzet}")
                await self.send(msg)
                self.set_next_state("CekanjeNaPonudu")
            else:
                self.agent.trenutna_ponuda['prihvaceno'] = True
                self.agent.trenutna_ponuda['cijena'] = self.agent.trenutna_cijena
                msg = Message(to=self.agent.aukcioner,body=json.dumps(self.agent.trenutna_ponuda),metadata={"ontology":"aukcija"})
                print(f"{self.agent.naziv}: Saljem poruku aukcioneru da prihvacam ponudu sa cijenom:", self.agent.trenutna_ponuda['cijena'])
                await self.send(msg)
                self.set_next_state("CekanjeNaPonudu")
