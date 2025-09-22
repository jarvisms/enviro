from enviro import logging
from enviro.constants import UPLOAD_SUCCESS, UPLOAD_FAILED
from enviro.mqttsimple import MQTTClient
import enviro.helpers as helpers
import ujson
import config

mqtt_client = None

def log_destination():
  logging.info(f"> uploading cached readings to MQTT broker: {config.mqtt_broker_address}")

def upload_reading(reading):
  global mqtt_client
  nickname = reading["nickname"]
  
  try:
    mqtt_client.publish(f"enviro/{nickname}", ujson.dumps(reading), retain=True, qos=config.mqtt_qos)
    return UPLOAD_SUCCESS

  except Exception as exc:
    import sys, io
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    logging.debug(f"  - an exception occurred when uploading.", buf.getvalue())

  return UPLOAD_FAILED

def hass_discovery(board_type):
  server = config.mqtt_broker_address
  username = config.mqtt_broker_username
  password = config.mqtt_broker_password
  nickname = config.nickname

  def mqtt_discovery(name, device_class, unit, value_name, model ):
    nickname = config.nickname
    from ucollections import OrderedDict
    obj = OrderedDict({
      "dev":
      {
        "ids":[nickname],
        "name":nickname,
        "mdl":"Enviro " + model,
        "mf":"Pimoroni"
      },
      "unit_of_meas":unit,
      "dev_cla":device_class,
      "val_tpl":"{{ value_json.readings." + value_name +" }}",
      "state_cla": "measurement",
      "stat_t":"enviro/" + nickname,
      "name":name,
      "uniq_id":"sensor." + nickname + "." + value_name,
    })
    try:
      # attempt to publish reading
      mqtt_client.publish(f"homeassistant/sensor/{nickname}/{value_name}/config", ujson.dumps(obj), retain=True)
      return UPLOAD_SUCCESS
    except Exception as exc:
      import sys, io
      buf = io.StringIO()
      sys.print_exception(exc, buf)
      logging.debug(f"  - an exception occurred during mqtt discovery", buf.getvalue())

  try:
    if config.mqtt_broker_ca_file:
    # Using SSL
      f = open("ca.crt")
      ssl_data = f.read()
      f.close()
      mqtt_client = MQTTClient(nickname, server, user=username, password=password, keepalive=60,
                               ssl=True, ssl_params={'cert': ssl_data})
    else:
    # Not using SSL
      mqtt_client = MQTTClient(nickname, server, user=username, password=password, keepalive=60)
    mqtt_client.connect()
  except Exception as exc:
    import sys, io
    buf = io.StringIO()
    sys.print_exception(exc, buf)
    logging.debug(f"  - an exception occurred during mqtt discovery", buf.getvalue())
  mqtt_discovery("Enviro Temperature", "temperature", "°C", "temperature", board_type) # Temperature
  mqtt_discovery("Enviro Pressure", "pressure", "hPa", "pressure", board_type) # Pressure
  mqtt_discovery("Enviro Humidity", "humidity", "%", "humidity", board_type) # Humidity
  mqtt_discovery("Enviro Voltage", "voltage", "V", "voltage", board_type) # Voltage
  if (board_type == "weather"):
    mqtt_discovery("Enviro Luminance", "illuminance", "lx", "luminance", board_type) # Luminance
    mqtt_discovery("Enviro Wind Speed", "wind_speed", "m/s", "wind_speed", board_type) # Wind Speed
    mqtt_discovery("Enviro Rain", "precipitation", "mm", "rain", board_type) # Rain
    mqtt_discovery("Enviro Rain Per Second", "precipitation", "mm/s", "rain_per_second", board_type) # Rain Per Second
    mqtt_discovery("Enviro Wind Direction", None, "°", "wind_direction", board_type) # Wind Direction //HASS doesn't have a device class for direction//
  elif (board_type == "grow"):
    mqtt_discovery("Enviro Luminance", "illuminance", "lx", "luminance", board_type) # Luminance
    mqtt_discovery("Enviro Moisture A", "humidity", "%", "moisture_a", board_type) # Moisture A
    mqtt_discovery("Enviro Moisture B", "humidity", "%", "moisture_b", board_type) # Moisture B
    mqtt_discovery("Enviro Moisture C", "humidity", "%", "moisture_c", board_type) # Moisture C
  elif (board_type == "indoor"):
    mqtt_discovery("Enviro Luminance", "illuminance", "lx", "luminance", board_type) # Luminance
    mqtt_discovery("Enviro Gas Resistance", None, "Ω", "gas_resistance", board_type) # Gas Resistance //HASS doesn't support resistance as a device class//
    mqtt_discovery("Enviro AQI", "aqi", None, "aqi", board_type) # AQI
    mqtt_discovery("Enviro Colour Temperature", "temperature", "K", "color_temperature", board_type) # Colo(u)r Temperature
  elif (board_type == "urban"):
    mqtt_discovery("Enviro Noise", "voltage", "V", "noise", board_type) # Noise
    mqtt_discovery("Enviro PM1", "pm1", "µg/m³", "pm1", board_type) # PM1
    mqtt_discovery("Enviro PM2.5", "pm25", "µg/m³", "pm2_5", board_type) # PM2_5
    mqtt_discovery("Enviro PM10", "pm10", "µg/m³", "pm10", board_type) # PM10
  mqtt_client.disconnect()

def connect():
  global mqtt_client
  server = config.mqtt_broker_address
  username = config.mqtt_broker_username
  password = config.mqtt_broker_password
  
  if config.mqtt_broker_ca_file:
  # Using SSL
    f = open("ca.crt")
    ssl_data = f.read()
    f.close()
    mqtt_client = MQTTClient(helpers.uid(), server, user=username, password=password, keepalive=60,
                              ssl=True, ssl_params={'cert': ssl_data})
  else:
  # Not using SSL
    mqtt_client = MQTTClient(helpers.uid(), server, user=username, password=password, keepalive=60)
  # Now continue with connection and upload
  mqtt_client.connect()

def disconnect():
  global mqtt_client
  mqtt_client.disconnect()
  mqtt_client = None
