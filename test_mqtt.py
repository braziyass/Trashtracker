import paho.mqtt.publish as publish

BROKER = "broker.hivemq.com"

publish.single("city/bin/1/status", "FULL", hostname=BROKER)
print("STATUS = FULL envoyé")

publish.single("city/bin/1/alert", "ANIMAL", hostname=BROKER)
