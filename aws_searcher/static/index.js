const socket = io.connect('http://' + document.domain + ':' + location.port)

socket.on('connect', () => {socket.emit('connected')})

socket.on('jobs', (response) => {
    data = response.data
    console.log(data)
    $('#jobsTable').DataTable({
        data: data.rows,
        columns: data.headers
    })
})