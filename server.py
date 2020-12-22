from aiohttp import web
from jsonrpcserver import method, async_dispatch as dispatch
from pymata_express import pymata_express

import aiohttp_cors


_pin_modes = {
  0: 'digital_input',
  1: 'digital_output',
  2: 'analog_input',
  3: 'pwm',
  4: 'servo',
  6: 'i2c',
  8: 'stepper',
  11: 'digital_input_pullup',
  12: 'sonar',
  13: 'tone',
  15: 'dht',
}

_board = None


@method
async def get_analog_map():
    data = await get_board().get_analog_map()
    pin_map = {}
    max_pin = -1
    for i in range(len(data)):
        if data[i] != 127:
            if data[i] > max_pin:
                max_pin = data[i]
            pin_map[data[i]] = i
    pins = [None] * (max_pin + 1)
    for k, v in pin_map.items():
        pins[k] = v
    return pins


@method
async def get_capabilities():
    data = await get_board().get_capability_report()
    pins = []
    x = 0
    while x < len(data):
        pin = {}
        while data[x] != 127:
            mode = _pin_modes.get(data[x])
            x += 1
            bits = data[x]
            x += 1
            pin[mode] = bits
        pins.append(pin)
        x += 1
    return pins


@method
async def set_pin_mode_analog_input(pin):
    await get_board().set_pin_mode_analog_input(pin)


@method
async def set_pin_mode_digital_input(pin):
    await get_board().set_pin_mode_digital_input(pin)


@method
async def set_pin_mode_digital_input_pullup(pin):
    await get_board().set_pin_mode_digital_input_pullup(pin)


@method
async def set_pin_mode_digital_output(pin):
    await get_board().set_pin_mode_digital_output(pin)


@method
async def set_pin_mode_pwm_output(pin):
    await get_board().set_pin_mode_pwm_output(pin)


@method
async def set_pin_mode_dht(pin, sensor_type):
    await get_board().set_pin_mode_dht(pin, sensor_type)


@method
async def set_pin_mode_servo(pin, min_pulse, max_pulse):
    await get_board().set_pin_mode_servo(pin, min_pulse, max_pulse)


@method
async def set_pin_mode_sonar(trigger_pin, echo_pin):
    await get_board().set_pin_mode_sonar(trigger_pin, echo_pin)


@method
async def set_pin_mode_stepper(steps_per_revolution, stepper_pins):
    await get_board().set_pin_mode_stepper(steps_per_revolution, stepper_pins)


@method
async def set_pin_mode_tone(pin):
    await get_board().set_pin_mode_tone(pin)


@method
async def digital_read(pin):
    value, _ = await get_board().digital_read(pin)
    return value


@method
async def analog_read(pin):
    value, _ = await get_board().analog_read(pin)
    return value


@method
async def digital_write(pin, value):
    await get_board().digital_write(pin, value)


@method
async def pwm_write(pin, value):
    await get_board().pwm_write(pin, value)


@method
async def dht_read(pin):
    h, t, _ = await get_board().dht_read(pin)
    return {
      'humidity':    h,
      'temperature': t
    }


@method
async def sonar_read(pin):
    value, _ = await get_board().sonar_read(pin)
    return value


@method
async def play_tone(pin, frequency, duration):
    await get_board().play_tone(pin, frequency, duration)


@method
async def play_tone_continuously(pin, frequency):
    await get_board().play_tone_continuously(pin, frequency)


@method
async def play_tone_off(pin):
    await get_board().play_tone_off(pin)


@method
async def servo_write(pin, position):
    await get_board().servo_write(pin, position)


@method
async def stepper_write(speed, steps):
    await get_board().stepper_write(speed, steps)


async def handle(request):
    request = await request.text()
    response = await dispatch(request)
    if response.wanted:
        return web.json_response(
            response.deserialized(),
            status=response.http_status,
        )
    else:
        return web.Response()


def get_board():
    global _board
    if not _board:
        raise Exception('board not connected')
    return _board


@method
async def connect():
    global _board
    if not _board:
        _board = pymata_express.PymataExpress(
            autostart=False,
            close_loop_on_shutdown=False,
        )
        await _board.start_aio()


@method
async def disconnect():
    global _board
    if _board:
        await _board.shutdown()
        _board = None


async def on_shutdown(app):
    await disconnect()
    

app = web.Application()
app.on_shutdown.append(on_shutdown)

cors = aiohttp_cors.setup(app, defaults={
  "http://www.eandb.ca": aiohttp_cors.ResourceOptions(
      allow_credentials=True,
      expose_headers="*",
      allow_headers="*",
  ),
  "http://bwkimmel.github.io": aiohttp_cors.ResourceOptions(
      allow_credentials=True,
      expose_headers="*",
      allow_headers="*",
  ),
})

cors.add(app.router.add_post("/", handle))

if __name__ == '__main__':
    web.run_app(app, port=4000)
