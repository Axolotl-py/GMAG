// =============================================
// CONSTANTES E CONFIGURAÇÕES GLOBAIS
// =============================================

const TEMAS = {
    CLARO: 'claro',
    ESCURO: 'escuro'
};

const PAGINAS = {
    INICIO: {
        titulo: 'Bem-vindo ao GMAP',
        conteudo: 'Escolha uma opção no menu para começar.'
    },
    CONFIGURACOES: {
        titulo: 'Configurações',
        conteudo: 'Aqui você poderá configurar o aplicativo.'
    }
};

const MAPEAMENTO_PAGINAS = {
    'Início': () => carregarPagina(PAGINAS.INICIO),
    'Configurações': () => carregarPagina(PAGINAS.CONFIGURACOES),
    'VSM': carregarVSM,
    'DRX': carregarDRX,
    'FMR': carregarFMR
};

// =============================================
// FUNÇÕES DE TEMA
// =============================================

function configurarTrocaDeTema() {
    const botaoTema = document.getElementById('themeToggle');
    const icones = {
        [TEMAS.CLARO]: '🌙',
        [TEMAS.ESCURO]: '☀️'
    };
    
    botaoTema.addEventListener('click', alternarTema);
    
    function alternarTema() {
        document.body.classList.toggle('light-theme');
        atualizarIconeTema();
        salvarPreferenciaTema();
    }
    
    function atualizarIconeTema() {
        const temaAtual = document.body.classList.contains('light-theme') ? TEMAS.CLARO : TEMAS.ESCURO;
        botaoTema.textContent = icones[temaAtual];
    }
    
    function salvarPreferenciaTema() {
        const tema = document.body.classList.contains('light-theme') ? TEMAS.CLARO : TEMAS.ESCURO;
        localStorage.setItem('tema', tema);
    }
    
    function carregarPreferenciaTema() {
        if (localStorage.getItem('tema') === TEMAS.CLARO) {
            document.body.classList.add('light-theme');
        }
        atualizarIconeTema();
    }
    
    carregarPreferenciaTema();
}

// =============================================
// FUNÇÕES DE NAVEGAÇÃO
// =============================================

function configurarNavegacaoSidebar() {
    document.querySelectorAll('.sidebar a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const pagina = this.textContent.trim();
            const handler = MAPEAMENTO_PAGINAS[pagina];
            
            if (handler) {
                handler();
            } else {
                carregarPagina({
                    titulo: pagina,
                    conteudo: 'Conteúdo indisponível no momento.'
                });
            }
        });
    });
}

// =============================================
// FUNÇÕES DE PÁGINAS
// =============================================

function carregarPagina(pagina) {
    const mainContent = document.querySelector('.main-content');
    mainContent.innerHTML = `
        <h1>${pagina.titulo}</h1>
        <p>${pagina.conteudo}</p>
    `;
}

function carregarVSM() {
    setMainContent(`
        <h1>VSM</h1>
        <p>Área de análise de VSM.</p>
        <div class="form-group">
            <label for="dir1">Diretório de Entrada 1:</label>
            <input type="text" id="dir1" class="form-control" placeholder="Selecione o diretório">
            <button onclick="selecionarDiretorio('dir1')" class="btn btn-secondary">Selecionar</button>
        </div>
        <div class="form-group">
            <label for="dir2">Diretório de Entrada 2:</label>
            <input type="text" id="dir2" class="form-control" placeholder="Selecione o diretório">
            <button onclick="selecionarDiretorio('dir2')" class="btn btn-secondary">Selecionar</button>
        </div>
        <div class="form-group">
            <label for="dir3">Diretório de Saída:</label>
            <input type="text" id="dir3" class="form-control" placeholder="Selecione o diretório">
            <button onclick="selecionarDiretorio('dir3')" class="btn btn-secondary">Selecionar</button>
        </div>
        <button onclick="processarVSM()" class="btn btn-primary">Executar VSM</button>
        <div id="statusVSM" class="mt-3"></div>
    `);
}

function carregarDRX() {
    setMainContent(`
        <h1>DRX</h1>
        <p>Área de análise de DRX.</p>
        <div class="form-group">
            <label for="arquivoDRX">Arquivo DRX:</label>
            <input type="file" id="arquivoDRX" class="form-control">
        </div>
        <div class="form-group">
            <label for="dirDRX">Diretório de Saída:</label>
            <input type="text" id="dirDRX" class="form-control" placeholder="Selecione o diretório">
            <button onclick="selecionarDiretorio('dirDRX')" class="btn btn-secondary">Selecionar</button>
        </div>
        <button onclick="enviarParaDRX()" class="btn btn-primary">Processar DRX</button>
        <div id="statusDRX" class="mt-3"></div>
    `);
}

function carregarFMR() {
    setMainContent(`
        <h1>FMR</h1>
        <p>Área de análise de FMR.</p>
        <div class="form-group">
            <label for="arquivoFMR">Arquivo FMR:</label>
            <input type="file" id="arquivoFMR" class="form-control">
        </div>
        <div class="form-group">
            <label for="dirFMR">Diretório de Saída:</label>
            <input type="text" id="dirFMR" class="form-control" placeholder="Selecione o diretório">
            <button onclick="selecionarDiretorio('dirFMR')" class="btn btn-secondary">Selecionar</button>
        </div>
        <button onclick="enviarParaFMR()" class="btn btn-primary">Processar FMR</button>
        <div id="statusFMR" class="mt-3"></div>
    `);
}

function setMainContent(html) {
    document.querySelector('.main-content').innerHTML = html;
}

// =============================================
// FUNÇÕES DE PROCESSAMENTO
// =============================================

async function selecionarDiretorio(idCampo) {
    try {
        const caminho = await eel.selecionar_diretorio()();
        document.getElementById(idCampo).value = caminho;
        mostrarStatus(`${idCampo} selecionado: ${caminho}`, `status${idCampo.replace('dir', '')}`);
    } catch (erro) {
        console.error('Erro ao selecionar diretório:', erro);
        mostrarStatus('Falha ao selecionar diretório. Por favor, tente novamente.', `status${idCampo.replace('dir', '')}`, true);
    }
}

async function processarVSM() {
    const dir1 = document.getElementById('dir1').value;
    const dir2 = document.getElementById('dir2').value;
    const dir3 = document.getElementById('dir3').value;
    const statusElement = document.getElementById('statusVSM');
    
    try {
        if (!dir1 || !dir2 || !dir3) {
            throw new Error('Por favor, selecione todos os diretórios.');
        }
        
        statusElement.innerHTML = '<div class="alert alert-info">Processando VSM... Aguarde.</div>';
        
        const resultado = await eel.processar_vsm(dir1, dir2, dir3)();
        
        statusElement.innerHTML = `<div class="alert alert-success">${resultado}</div>`;
    } catch (erro) {
        statusElement.innerHTML = `<div class="alert alert-danger">Erro: ${erro.message}</div>`;
    }
}

async function enviarParaDRX() {
    await processarArquivo('DRX');
}

// Função principal para processar FMR
async function processarFMR() {
    const arquivoInput = document.getElementById('arquivoFMR');
    const dirOutput = document.getElementById('dirFMR').value;
    const btnProcessar = document.getElementById('btnProcessarFMR');
    const statusElement = document.getElementById('statusFMR');
    const resultadosContainer = document.getElementById('resultadosFMR');
    
    // Validação
    if (!arquivoInput.files.length || !dirOutput) {
        showStatus('statusFMR', 'Por favor, selecione o arquivo e o diretório de saída', 'error');
        return;
    }
    
    try {
        // Configura estado de processamento
        btnProcessar.disabled = true;
        btnProcessar.innerHTML = '<span class="loading"></span> Processando...';
        resultadosContainer.innerHTML = '';
        showStatus('statusFMR', 'Preparando análise FMR...', 'warning');
        
        // Obtém parâmetros iniciais do formulário
        const parametrosIniciais = {
            a: parseFloat(document.getElementById('param_a').value) || 1,
            b: parseFloat(document.getElementById('param_b').value) || 0,
            c: parseFloat(document.getElementById('param_c').value) || 1,
            d: parseFloat(document.getElementById('param_d').value) || 0.8,
            Hr1: parseFloat(document.getElementById('param_hr1').value) || 1000,
            dH1: parseFloat(document.getElementById('param_dh1').value) || 50,
            Hr2: parseFloat(document.getElementById('param_hr2').value) || 1200,
            dH2: parseFloat(document.getElementById('param_dh2').value) || 50
        };
        
        // Chamada para o Python
        const resultado = await eel.processar_fmr(
            arquivoInput.files[0].path,
            dirOutput,
            parametrosIniciais
        )();
        
        // Tratamento do resultado
        if (resultado.success) {
            showStatus('statusFMR', resultado.message, 'success');
            exibirResultadosFMR(resultado.resultados);
        } else {
            showStatus('statusFMR', resultado.message, 'error');
        }
    } catch (error) {
        showStatus('statusFMR', `Erro: ${error.message}`, 'error');
    } finally {
        btnProcessar.disabled = false;
        btnProcessar.textContent = 'Processar FMR';
    }
}


function exibirResultadosFMR(resultados) {
    const container = document.getElementById('resultadosFMR');
    container.innerHTML = `
        <div class="tabs">
            <button class="tab-btn active" onclick="abrirTab(event, 'resumo')">Resumo</button>
            <button class="tab-btn" onclick="abrirTab(event, 'graficos')">Gráficos por Ângulo</button>
            <button class="tab-btn" onclick="abrirTab(event, 'variacao')">Variação dos Parâmetros</button>
            <button class="tab-btn" onclick="abrirTab(event, 'comparacao')">Comparação entre Ângulos</button>
            <button class="tab-btn" onclick="abrirTab(event, 'dados')">Dados Completos</button>
        </div>
        
        <div id="resumo" class="tab-content" style="display:block">
            <h3>Resumo da Análise</h3>
            <p><strong>Ângulos processados:</strong> ${resultados.angulos.length}</p>
            <p><strong>Arquivos gerados:</strong> ${resultados.arquivos_gerados.length}</p>
            <p><strong>Diretório de saída:</strong> ${os.path.dirname(resultados.relatorio_path)}</p>
            
            <div class="card" style="margin-top: 20px;">
                <h4>Ações Rápidas</h4>
                <button onclick="abrirDiretorio('${os.path.dirname(resultados.relatorio_path)}')">
                    Abrir Diretório de Resultados
                </button>
                <button onclick="visualizarRelatorio('${resultados.relatorio_path}')">
                    Visualizar Relatório Completo
                </button>
            </div>
        </div>
        
        <div id="graficos" class="tab-content">
            <h3>Gráficos por Ângulo</h3>
            <div class="gallery" id="gallery-angulos"></div>
        </div>
        
        <div id="variacao" class="tab-content">
            <h3>Variação dos Parâmetros</h3>
            <img src="${resultados.grafico_variacao}" alt="Variação dos parâmetros" class="img-responsive">
            <button onclick="visualizarGrafico('${resultados.grafico_variacao}')" style="margin-top: 10px;">
                Ampliar Gráfico
            </button>
        </div>
        
        <div id="comparacao" class="tab-content">
            <h3>Comparação entre Ângulos</h3>
            <img src="${resultados.grafico_comparacao}" alt="Comparação entre ângulos" class="img-responsive">
            <button onclick="visualizarGrafico('${resultados.grafico_comparacao}')" style="margin-top: 10px;">
                Ampliar Gráfico
            </button>
        </div>
        
        <div id="dados" class="tab-content">
            <h3>Dados Completos</h3>
            <div class="card">
                <button onclick="copiarDados()" style="margin-bottom: 10px;">
                    Copiar Dados para Área de Transferência
                </button>
                <pre id="dados-completos"></pre>
            </div>
        </div>
    `;
    
    // Preenche a galeria de gráficos
    const gallery = document.getElementById('gallery-angulos');
    resultados.graficos_angulo.forEach(grafico => {
        const angulo = grafico.split('_').slice(-1)[0].replace('.png', '');
        gallery.innerHTML += `
            <div class="gallery-item">
                <img src="${grafico}" alt="Gráfico FMR" class="img-thumbnail" 
                     onclick="visualizarGrafico('${grafico}')">
                <div class="gallery-caption">
                    Ângulo ${angulo}°
                    <button onclick="visualizarGrafico('${grafico}')" class="btn-small">
                        Ampliar
                    </button>
                </div>
            </div>
        `;
    });
    
    // Exibe os dados completos
    document.getElementById('dados-completos').textContent = 
        JSON.stringify(resultados, null, 2);
}

// Funções auxiliares para as abas
function abrirTab(evt, tabName) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }
    
    const tabButtons = document.getElementsByClassName("tab-btn");
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }
    
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

async function visualizarGrafico(caminho) {
    const success = await eel.visualizar_grafico(caminho)();
    if (!success) {
        alert("Não foi possível abrir o gráfico. Verifique se o arquivo existe.");
    }
}

async function abrirDiretorio(caminho) {
    await eel.selecionar_diretorio()(caminho);
}

function copiarDados() {
    const dados = document.getElementById('dados-completos').textContent;
    navigator.clipboard.writeText(dados)
        .then(() => alert("Dados copiados para a área de transferência!"))
        .catch(err => alert("Erro ao copiar dados: " + err));
}

function visualizarRelatorio(caminho) {
    visualizarGrafico(caminho);
}

function showStatus(elementId, message, type = 'success') {
    const element = document.getElementById(elementId);
    element.className = `status-message ${type}`;
    element.innerHTML = message;
}

async function processarArquivo(tipo) {
    const inputArquivo = document.getElementById(`arquivo${tipo}`);
    const inputDiretorio = document.getElementById(`dir${tipo}`);
    const statusElement = document.getElementById(`status${tipo}`);
    const botao = event.target;
    
    try {
        // Validação
        if (!inputArquivo.files.length || !inputDiretorio.value) {
            throw new Error(`Por favor, selecione o arquivo e o diretório para ${tipo}`);
        }
        
        // Feedback visual
        botao.disabled = true;
        botao.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...';
        
        statusElement.innerHTML = '<div class="alert alert-info">Processando arquivo... Aguarde.</div>';
        
        // Processamento
        const resultado = await eel[`processar_${tipo.toLowerCase()}`](
            inputArquivo.files[0].path, 
            inputDiretorio.value
        )();
        
        statusElement.innerHTML = `<div class="alert alert-success">${resultado}</div>`;
    } catch (erro) {
        statusElement.innerHTML = `<div class="alert alert-danger">Erro no processamento ${tipo}: ${erro.message}</div>`;
    } finally {
        botao.disabled = false;
        botao.textContent = `Processar ${tipo}`;
    }
}

function mostrarStatus(mensagem, elementoId, isErro = false) {
    const elemento = document.getElementById(elementoId);
    if (elemento) {
        const classe = isErro ? 'alert-danger' : 'alert-success';
        elemento.innerHTML = `<div class="alert ${classe}">${mensagem}</div>`;
    }
}

// =============================================
// INICIALIZAÇÃO DO APLICATIVO
// =============================================

document.addEventListener('DOMContentLoaded', function() {
    configurarTrocaDeTema();
    configurarNavegacaoSidebar();
    carregarPagina(PAGINAS.INICIO);
    
    console.log('Aplicativo GMAP inicializado com sucesso!');
});