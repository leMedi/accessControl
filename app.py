from server import app

# start http server
app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
