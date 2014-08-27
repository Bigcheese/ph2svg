from ph2svg.ph2svg import ph2svg

def application(env, start_response):
  return ph2svg(env, start_response)
