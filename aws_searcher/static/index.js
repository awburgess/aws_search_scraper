const socket = io.connect('http://' + document.domain + ':' + location.port)

let queue = []
let jobsTable
let inProcess = false

socket.on('connect', () => {socket.emit('connected')})

$(document).on('click', '.job', (e) => {
    const target = e.currentTarget.firstChild
    const result = target.innerText || target.textContent
    if (parseInt(result)) {
        socket.emit('getJob', {job: parseInt(result)})
    }
})

$(document).ready(() => {
    $('#submit').click(() => {
        const category = $('#categories').find(":selected").text()
        const terms = $('#terms').val()
        const market = $('#markets').find(":selected").val()
        if (inProcess)
            queue.push({category: category, terms: terms})
        else {
            inProcess = true
            socket.emit('submit', {category: category, terms: terms, market: market})
        }
    })
})

const addTableRowClass = () => {
    const rows = $('#jobsTable').children("tbody").children();
    $(rows).each((index, el) => {
        $(el).addClass('job')
    })
}

const addNewJobRows = (rows) => {
    jobsTable.settings.dataset.originalRecords = rows
    jobsTable.process()
}

$(document).on('click', '#close', () => {
    $('#results').css('width', '0%')
    $('#results').empty()
    $('#results').append("<span id='close'><i class=\"fa fa-times fa-2x\"></i></span><br/>" +
        "<table id=\"result\" class=\"table table-bordered\">\n" +
        "      <thead id=\"resultHeaders\">\n" +
        "      </thead>\n" +
        "      <tbody>\n" +
        "      </tbody>\n" +
        "    </table>")

})

socket.on('jobCheck', (response) => {
    data = response.data
    let processing = false
    data.rows.forEach((row) => {
        if (row.status === 'Processing')
            processing = true
    })
    if (!processing && inProcess)
        inProcess = false
    addNewJobRows(data.rows)
})

socket.on('jobs', (response) => {
    data = response.data
    jobsTable = $('#jobsTable').dynatable({
        dataset: {
            records: data.rows
        }
    }).bind('dynatable:afterProcess', addTableRowClass).data('dynatable')

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

    $('#result').dynatable({
        table: {
            headRowSelector: '#resultHeaders',
            defaultColumnIdStyle: 'lowercase',
        },
        dataset: {
            records: rows
        }
    })

    $('#results').css('width', '100%')
})

setInterval(() => {
    socket.emit('jobUpdates')
}, 5000)


