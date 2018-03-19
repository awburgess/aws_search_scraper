const socket = io.connect('http://' + document.domain + ':' + location.port)

socket.on('connect', () => {socket.emit('connected')})

$(document).on('click', '.jobid', (e) => {
    const result = e.target.innerText
    if (parseInt(result)) {
        socket.emit('getJob', {job: parseInt(result)})
    }
})

// TODO: Finish submitting jobs
$(document).ready(() => {
    $('#submit').click()
})

socket.on('jobs', (response) => {
    data = response.data
    $('#jobsTable').DataTable({
        data: data.rows,
        columns: data.headers
    })
})

socket.on('jobResult', (response) => {
    const rows = response.rows
    const rowHeaders = response.row_headers
    const relationshipRows = response.relationships
    const relationshipHeaders = response.relationship_headers

    $('#rowsTable').DataTable({
        data: rows,
        columns: rowHeaders,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel', 'pdf', 'print'
        ]
    })

    $('#fullScreen').addClass('in')
})



