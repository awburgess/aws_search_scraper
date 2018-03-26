const socket = io.connect('http://' + document.domain + ':' + location.port)

socket.on('connect', () => {socket.emit('connected')})

$(document).on('click', '.job', (e) => {
    const target = e.currentTarget.firstChild
    const result = target.innerText || target.textContent
    console.log(result)
    if (parseInt(result)) {
        socket.emit('getJob', {job: parseInt(result)})
    }
})

// TODO: Finish submitting jobs
$(document).ready(() => {
    $('#submit').click()
})

const addTableRowClass = () => {
    const rows = $('#jobsTable').children("tbody").children();
    $(rows).each((index, el) => {
        $(el).addClass('job')
    })
}

$(document).on('click', '#close', () => {
    $('#results').css('width', '0%')
})

socket.on('jobs', (response) => {
    data = response.data
    $('#jobsTable').dynatable({
        dataset: {
            records: data.rows
        }
    }).bind('dynatable:afterProcess', addTableRowClass)

    addTableRowClass()
})

socket.on('jobResult', (response) => {
    const rows = response.rows
    const rowHeaders = response.row_headers
    const relationshipRows = response.relationships
    const relationshipHeaders = response.relationship_headers

    $.each(rowHeaders, (index, value) => {
        $('#resultHeaders').append('<th>' + value + '</th>')
    })

    console.log(rows)

    $('#rowsTable').dynatable({
        table: {
            defaultColumnIdStyle: 'lowercase'
        },
        dataset: {
            records: rows
        }
    })

    $('#results').css('width', '100%')
})



