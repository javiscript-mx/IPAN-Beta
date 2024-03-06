$('.menu .item').tab()
$(document).ready(function () {
  $('.analiticsData').hide()
  $('.menu .item').tab()
  $('#errorMessage').hide()
  $('#progressBar').hide()
})
//var server = 'http://127.0.0.1:5001'
var server = 'https://test-njeyriclya-uc.a.run.app'
var lockFlagSearchEngine = 0
function buscarPatentes() {
  if (lockFlagSearchEngine == 0) {
    resetPage(1)
    $('#resultadoBusqueda').addClass('loading segment')
    $('#progressBar').show()
    var query = document.getElementById('query').value
    fetch(server + '/api/buscar_patentes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: query }),
    })
      .then((response) => response.json())
      .then((data) => {
        updateProgressBar(10)
        analizarPatentes()
        procesarPatentes()
        procesarPatentes2()
      })
      .catch((error) => {
        $('#errorMessage').show()
        resetPage(0)
        console.error('Error:', error)
      })
  }
}

function analizarPatentes() {
  var query = document.getElementById('query').value
  fetch(server + '/api/analizar_patentes', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: query }),
  })
    .then((response) => response.json())
    .then((data) => {
      lockFlagSearchEngine = 0
      updateProgressBar(30)
      $('#progressBar').hide()
      $('.analiticsData').show()
      $('.infoMessage').hide()
      $('#resultadoBusqueda').removeClass('loading segment')
      google.charts.setOnLoadCallback(drawFechaPublicacionChart)
      google.charts.setOnLoadCallback(drawPieChart)

      drawFechaPublicacionChart(
        orderDates(data.analisisFechasPublicacion),
        'fechasPublicacionChart',
      )
      drawFechaPublicacionChart(
        orderDates(data.analisisFechasSolicitud),
        'fechasSolicitudChart',
      )
      $('#totalAplicaciones').text(data.totalAplicaciones)
      $('#totalPublicaciones').text(data.totalPublicaciones)
      $('#paisesUnicos').text(data.paisesUnicos)
      drawPieChart(data.patentesPorPais, 'patentesPorPais')
      drawPieChart(data.palabrasClaveTitulos, 'palabrasClaveTitulos')
      drawPieChart(data.palabrasClaveResumen, 'palabrasClaveResumen')
    })
    .catch((error) => {
      $('#errorMessage').show()
      resetPage(0)
      console.error('Error:', error)
    })
}

function procesarPatentes() {
  var query = document.getElementById('query').value
  fetch(server + '/api/procesar_patentes', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: query }),
  })
    .then((response) => response.json())
    .then((data) => {
      updateProgressBar(30)
      $('#recordsPerPage').on('change', function () {
        var selectedValue = $(this).val()
        displayData(data.results, 1, selectedValue, 'table')
        setupPagination(data.results, 1, selectedValue, 'pagination', 'table')
      })
      displayData(data.results, 1, $('#recordsPerPage').val(), 'table')
      setupPagination(
        data.results,
        1,
        $('#recordsPerPage').val(),
        'pagination',
        'table',
      )
      //$('#totalRegistros').val(data.results.length()) Implementar mas tarde
    })
    .catch((error) => {
      $('#errorMessage').show()
      resetPage(0)
      console.error('Error:', error)
    })
}

function procesarPatentes2() {
  updateProgressBar(30)
  var query = document.getElementById('query').value
  fetch(server + '/api/procesar_patentes2', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: query }),
  })
    .then((response) => response.json())
    .then((data) => {
      $('#recordsPerPage2').on('change', function () {
        var selectedValue = $(this).val()
        displayData(data.results, 1, selectedValue, 'table2')
        setupPagination(data.results, 1, selectedValue, 'pagination2', 'table2')
      })
      displayData(data.results, 1, $('#recordsPerPage2').val(), 'table2')
      setupPagination(
        data.results,
        1,
        $('#recordsPerPage2').val(),
        'pagination2',
        'table2',
      )
      //$('#totalRegistros').val(data.results.length()) Implementar mas tarde
    })
    .catch((error) => {
      $('#errorMessage').show()
      resetPage(0)
      console.error('Error:', error)
    })
}

google.charts.load('current', { packages: ['corechart'] })

function drawFechaPublicacionChart(data, idchart) {
  var datos = Object.entries(data)
  datos.unshift(['Fechas', 'Cantidades'])

  var data = google.visualization.arrayToDataTable(datos)

  if (idchart == 'fechasPublicacionChart') {
    var hAxisTitle = 'Fechas de publicación'
    var chartTitle = 'Datos de fechas de publicación por fecha'
  } else {
    var hAxisTitle = 'Fechas de solicitud'
    var chartTitle = 'Datos de fechas de solicitud por fecha'
  }

  // Opciones del gráfico
  var options = {
    title: chartTitle,
    hAxis: { title: hAxisTitle, titleTextStyle: { color: '#333' } },
    vAxis: { minValue: 0 },
  }

  // Crear el gráfico de barras
  var chart = new google.visualization.ColumnChart(
    document.getElementById(idchart),
  )
  chart.draw(data, options)
}

function drawPieChart(data, idchart) {
  if (idchart == 'patentesPorPais') {
    var chartTitle = 'Conteo de patentes por pais'
    var axisNames = ['Paises', 'Cantidades']
  } else if (idchart == 'palabrasClaveTitulos') {
    var chartTitle = 'Conteo de palabras clave por titulo'
    var axisNames = ['Palabras', 'Cantidades']
  } else {
    var chartTitle = 'Conteo de palabras clave por resumen'
    var axisNames = ['Palabras', 'Cantidades']
  }

  var datos = Object.entries(data)

  datos.unshift(axisNames)

  var data = google.visualization.arrayToDataTable(datos)

  var options = {
    title: chartTitle,
  }

  var chart = new google.visualization.PieChart(
    document.getElementById(idchart),
  )
  chart.draw(data, options)
}

function displayData(data, currentPage, recordsPerPage, idtable) {
  var table = document.getElementById(idtable).getElementsByTagName('tbody')[0]
  var start = (currentPage - 1) * recordsPerPage
  var end = start + recordsPerPage
  var paginatedData = data.slice(start, end)

  table.innerHTML = ''

  paginatedData.forEach(function (item) {
    var similarity_score = (item.similarity * 5).toFixed(3)
    var similarity = ((item.similarity * 5) / item.TopScore).toFixed(3)
    var row = table.insertRow()
    row.insertCell(0).innerHTML = item.Title
    row.insertCell(1).innerHTML = item.Abstract
    row.insertCell(2).innerHTML = item.Inventors
    row.insertCell(3).innerHTML = item.Country
    row.insertCell(4).innerHTML = item.PublicationDate
    row.insertCell(5).innerHTML =
      '<div class="ui yellow rating" data-icon="star" data-rating="' +
      similarity +
      '" data-max-rating="5"></div>'
    row.insertCell(6).innerHTML = similarity_score // + ' de 5'
    $('.ui.rating').rating()
  })
}

function setupPagination(
  data,
  currentPage,
  recordsPerPage,
  idpagination,
  idtable,
) {
  var pagination = document.getElementById(idpagination)
  pagination.innerHTML = ''

  var pageCount = Math.ceil(data.length / recordsPerPage)

  for (var i = 1; i <= pageCount; i++) {
    var btn = document.createElement('a')
    btn.classList.add('item')
    btn.innerHTML = i
    btn.addEventListener('click', function () {
      currentPage = parseInt(this.innerHTML)
      displayData(data, currentPage, recordsPerPage, idtable)
      var currentBtn = document.querySelector(
        '#' + idpagination + ' .active.item',
      )
      if (currentBtn) {
        currentBtn.classList.remove('active')
      }
      this.classList.add('active')
    })
    pagination.appendChild(btn)
  }
}

function updateProgressBar(progress) {
  $('#progressBar').progress({
    percent: progress,
  })
}

function resetPage(flag) {
  lockFlagSearchEngine = flag
  $('.infoMessage').show()
  $('.analiticsData').hide()
  $('#progressBar').hide()
  $('#resultadoBusqueda').removeClass('loading segment')
}

function orderDates(datesObject) {
  // Convertir el objeto en un array de pares clave-valor
  const arrayDatos = Object.entries(datesObject)

  // Ordenar el array de pares clave-valor en función de las fechas
  arrayDatos.sort((a, b) => {
    const fechaA = new Date(a[0].split('.').reverse().join('-'))
    const fechaB = new Date(b[0].split('.').reverse().join('-'))
    return fechaA - fechaB
  })

  // Reconstruir el objeto a partir del array ordenado
  const datosOrdenados = {}
  arrayDatos.forEach((item) => {
    datosOrdenados[item[0]] = item[1]
  })
  return datosOrdenados
}
