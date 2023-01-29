import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from slika import Slika
from random import randrange
from spade.message import Message
import json

class Aukioner(Agent):
    def __init__(self, jid, password, kupac1, kupac2): 
        super().__init__(jid, password)
        self.slika1 = Slika(100,"Slika1","Pero Peric")
        self.slika2 = Slika(150,"Slika2","Petar Peric")
        self.slika3 = Slika(200,"Slika3","Ante Peric")
        self.slika4 = Slika(150, "Slika4", "Marko Markic")
        self.slika5 = Slika(300, "Slika5", "Ivan Ivic")
        self.slika6 = Slika(350, "Slika6", "Luka Lukic")
        self.kupac1 = kupac1
        self.kupac2 = kupac2
        self.lista_slika = [self.slika1, self.slika2, self.slika3, self.slika4, self.slika5, self.slika6]
        
    class AukcionerPonasanje(FSMBehaviour):
        async def on_start(self):
            print("Pokrecem aukcionera..")

        async def on_end(self):
            print("Završavam aukcionera..")
        
    async def setup(self):
        fsm = self.AukcionerPonasanje()
        fsm.add_state(name="PocetnaPonuda", state=self.PocetnaPonuda(),initial=True)
        fsm.add_state(name="CekanjeNaPonuduKupca", state=self.CekanjeNaPonuduKupca())
        fsm.add_state(name="CekanjeNaPocetnuPonudu", state=self.CekanjeNaPocetnuPonudu())

        fsm.add_transition(source="PocetnaPonuda", dest= "CekanjeNaPonuduKupca")
        fsm.add_transition(source="CekanjeNaPonuduKupca", dest="PocetnaPonuda")
        fsm.add_transition(source="CekanjeNaPonuduKupca", dest="CekanjeNaPonuduKupca")
        fsm.add_transition(source="CekanjeNaPonuduKupca", dest="CekanjeNaPocetnuPonudu")
        fsm.add_transition(source="CekanjeNaPocetnuPonudu", dest="PocetnaPonuda")
        fsm.add_transition(source="CekanjeNaPocetnuPonudu", dest="CekanjeNaPocetnuPonudu")
        self.add_behaviour(fsm)

    class PocetnaPonuda(State):
        async def run(self):
            if len(self.agent.lista_slika) > 0:
                slika_za_prodaju = self.agent.lista_slika.pop(randrange(len(self.agent.lista_slika)))
                slika_za_prodaju_json = {'cijena': slika_za_prodaju.cijena, 'naziv_slike':slika_za_prodaju.naziv_slike, 'naziv_autora':slika_za_prodaju.naziv_autora, 'prihvaceno': True}
                msg = Message(to=self.agent.kupac1,body=json.dumps(slika_za_prodaju_json),metadata={"ontology":"aukcija"})
                await self.send(msg)
                print(f"Aukcioner: Šaljem pocetnu ponudu za sliku: {slika_za_prodaju_json['naziv_slike']} sa cijenom {slika_za_prodaju_json['cijena']}")
                self.set_next_state("CekanjeNaPonuduKupca")
            else: 
                print("Aukcioner: Prodane su sve slike. Završavam aukciju.")
                msg1 = Message(to=self.agent.kupac1,body=json.dumps({'gotovo': True}),metadata={"ontology":"aukcija"})
                await self.send(msg1)
                msg2 = Message(to=self.agent.kupac2,body=json.dumps({'gotovo': True}),metadata={"ontology":"aukcija"})
                await self.send(msg2)
                await self.agent.stop()

    class CekanjeNaPonuduKupca(State):
        async def run(self):
            msg = await self.receive(timeout=30)
            if msg:
                poruka_kupca = json.loads(msg.body)
                ponuditelj = msg.sender[:6]
                if ponuditelj[0] == "kupac1":
                    kupac_odgovor = self.agent.kupac2
                    kupac_odgovor_ime = "Kupac 2"
                else:
                    kupac_odgovor = self.agent.kupac1
                    kupac_odgovor_ime = "Kupac 1"
                prihvaceno = poruka_kupca['prihvaceno'] 
                if prihvaceno:
                    msg = Message(to=kupac_odgovor,body=msg.body,metadata={"ontology":"aukcija"})
                    await self.send(msg)
                    self.set_next_state("CekanjeNaPonuduKupca")
                else:
                    print(f"Aukcioner: kupac {kupac_odgovor_ime} je pobijedio i kupio sliku {poruka_kupca['naziv_slike']} za cijenu {poruka_kupca['cijena']}")
                    msg = Message(to=kupac_odgovor,body=msg.body,metadata={"ontology":"aukcija"})
                    await self.send(msg)
                    self.set_next_state("CekanjeNaPocetnuPonudu")
                
            else:
                print("Aukcioner: Čekao sam na ponudu kupca, ali nije pristigla.")
                self.set_next_state("CekanjeNaPonuduKupca")

    class CekanjeNaPocetnuPonudu(State):
        async def run(self):
            msg = await self.receive(timeout=30)
            if msg:
                poruka_kupca = json.loads(msg.body)
                if "spremno" in poruka_kupca:
                    self.set_next_state("PocetnaPonuda")
                else:
                    print("Aukcioner: Čekao sam da kupac bude spreman na novu pocetnu ponudu, ali nije pristigla.")
                    self.set_next_state("CekanjeNaPocetnuPonudu")
            else:
                print("Aukcioner: Čekao sam da kupac bude spreman na novu pocetnu ponudu, ali nije pristigla.")
                self.set_next_state("CekanjeNaPocetnuPonudu")
            
            