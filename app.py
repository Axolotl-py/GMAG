import eel
import os
import json
import sys
import traceback
import tkinter as tk
from tkinter import filedialog
import GMAG  # Sua biblioteca de análise
from datetime import datetime
import numpy as np, matplotlib.pyplot as plt, os, pandas as pd, scipy.optimize as spy, lmfit
class AjustadorMultiplosAngulos:
    def __init__(self, caminho_arquivo):
        self.caminho_arquivo = caminho_arquivo
        self.dados_completos = None
        self.angulos_disponiveis = None
        self.resultados = {}
        self.carregar_dados()
        
    def carregar_dados(self):
        """Carrega e organiza os dados por ângulo"""
        try:
            with open(self.caminho_arquivo, 'r') as f:
                linhas = f.readlines()
            
            dados = []
            for linha in linhas:
                if not linha.strip() or linha.strip().startswith(('Filename:', '#')):
                    continue
                
                valores = linha.split()
                if len(valores) >= 3:
                    try:
                        linha_float = [float(v.replace(',', '.')) for v in valores[:3]]
                        dados.append(linha_float)
                    except ValueError:
                        continue
            
            if not dados:
                raise ValueError("Nenhum dado numérico válido encontrado")
            
            self.dados_completos = np.array(dados)
            self.angulos_disponiveis = np.unique(self.dados_completos[:, 1])
            print(f"Ângulos encontrados: {self.angulos_disponiveis}")
                
        except Exception as e:
            print(f"Erro ao carregar dados: {str(e)}")
            raise

    @staticmethod
    def modelo(params, x, y=None):
        """Função modelo para o ajuste"""
        a = params['a']
        b = params['b']
        c = params['c']
        Hr1 = params['Hr1']
        dH1 = params['dH1']
        modelo = a + b * x + c * (x - Hr1) / ((x - Hr1)**2 + (dH1/2)**2)**2
        if y is None:
            return modelo
        return modelo - y

    def ajustar_angulo(self, angulo, parametros_iniciais):
        """Realiza o ajuste para um ângulo específico"""
        try:
            # Filtra dados para o ângulo especificado
            mascara = self.dados_completos[:, 1] == angulo
            x = self.dados_completos[mascara, 0]
            y = self.dados_completos[mascara, 2]
            
            if len(x) == 0:
                raise ValueError(f"Nenhum dado encontrado para o ângulo {angulo}")
            
            params = lmfit.Parameters()
            for nome, valor in parametros_iniciais.items():
                params.add(nome, value=valor)
                
            params['Hr1'].set(min=900, max=950)
            params['dH1'].set(min=0, max=100)
            
            # Cria o minimizador corretamente
            minimizer = lmfit.Minimizer(self.modelo, params, fcn_args=(x, y))
            
            # Executa o ajuste
            resultado = minimizer.minimize(method='leastsq')
            
            if not resultado.success:
                raise RuntimeError("O ajuste não convergiu")
            
            # Armazena resultados
            self.resultados[angulo] = {
                'x': x,
                'y': y,
                'resultado': resultado,
                'parametros': {
                    'a': resultado.params['a'].value,
                    'b': resultado.params['b'].value,
                    'c': resultado.params['c'].value,
                    'Hr1': resultado.params['Hr1'].value,
                    'dH1': resultado.params['dH1'].value
                }
            }
            
            return resultado
        
        except Exception as e:
            print(f"Erro no ajuste para ângulo {angulo}: {str(e)}")
            raise

    def plotar_angulo(self, angulo):
        """Plota os dados e o ajuste para um ângulo específico"""
        if angulo not in self.resultados:
            raise ValueError(f"Nenhum resultado encontrado para o ângulo {angulo}")
            
        dados = self.resultados[angulo]
        x = dados['x']
        y = dados['y']
        resultado = dados['resultado']
        
        plt.figure(figsize=(10, 6))
        plt.plot(x, y, 'bo', label=f'Dados (ângulo={angulo})')
        plt.plot(x, self.modelo(resultado.params, x), 
                'r-', lw=2, label='Curva Ajustada')
        plt.plot(x, y - self.modelo(resultado.params, x),
                'g--', alpha=0.5, label='Resíduos')
                
        plt.xlabel("Campo (Oe)", fontsize=12)
        plt.ylabel("Sinal (u.a.)", fontsize=12)
        plt.title(f"Análise para Ângulo {angulo}", fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plotar_comparacao(self):
        """Plota todos os ângulos juntos para comparação"""
        if not self.resultados:
            raise ValueError("Nenhum resultado disponível para plotar")
            
        plt.figure(figsize=(12, 8))
        
        for angulo in sorted(self.resultados.keys()):
            dados = self.resultados[angulo]
            plt.plot(dados['x'], dados['y'], 'o', label=f'Ângulo {angulo} (dados)')
            plt.plot(dados['x'], self.modelo(dados['resultado'].params, dados['x']), 
                    '-', label=f'Ângulo {angulo} (ajuste)')
        
        plt.xlabel("Campo (Oe)", fontsize=12)
        plt.ylabel("Sinal (u.a.)", fontsize=12)
        plt.title("Comparação entre Ângulos", fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

# Configuração de logging
LOG_FILE = 'gmag_app.log'

def setup_logging():
    """Configura o sistema de logging"""
    from logging import getLogger, FileHandler, Formatter, INFO
    logger = getLogger('GMAG')
    handler = FileHandler(LOG_FILE)
    handler.setFormatter(Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(INFO)
    return logger

logger = setup_logging()

# Configuração inicial do Eel
def initialize_eel():
    """Configura e inicializa o Eel"""
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
    eel.init(web_dir)

# Funções expostas para o JavaScript
@eel.expose
def selecionar_arquivo(extensoes=None):
    """Abre um seletor de arquivo com opções de filtro"""
    try:
        root = tk.Tk()
        root.withdraw()
        
        filetypes = [
            ('Arquivos de dados', '*.txt *.csv *.xlsx *.dat'),
            ('Todos os arquivos', '*.*')
        ]
        
        if extensoes:
            custom_types = [(f'Arquivos {ext.upper()}', f'*.{ext}') for ext in extensoes.split(',')]
            filetypes = custom_types + filetypes
            
        arquivo = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=filetypes
        )
        
        if arquivo:
            logger.info(f'Arquivo selecionado: {arquivo}')
            return arquivo
        return None
    except Exception as e:
        logger.error(f'Erro ao selecionar arquivo: {str(e)}')
        return None

@eel.expose
def processar_drx(arquivo, dir_saida=None):
    """Processa o arquivo para DRX com tratamento robusto"""
    try:
        if not arquivo or not os.path.exists(arquivo):
            raise FileNotFoundError("Arquivo não encontrado ou não selecionado")
        
        logger.info(f'Iniciando processamento DRX: {arquivo}')
        
        # Validação básica do arquivo
        if os.path.getsize(arquivo) == 0:
            raise ValueError("O arquivo está vazio")
        
        # Processamento principal
        resultado = GMAG.DRX(arquivo, output_dir=dir_saida)
        
        msg = f"Análise DRX concluída | Arquivo: {os.path.basename(arquivo)}"
        if dir_saida:
            msg += f" | Resultados em: {dir_saida}"
        
        logger.info(msg)
        return {
            'success': True,
            'message': msg,
            'result': str(resultado),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = f"Erro no processamento DRX: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'error_details': str(e),
            'timestamp': datetime.now().isoformat()
        }

@eel.expose
def selecionar_diretorio(titulo="Selecione um diretório"):
    """Abre seletor de diretório com título personalizável"""
    try:
        root = tk.Tk()
        root.withdraw()
        diretorio = filedialog.askdirectory(title=titulo)
        if diretorio:
            logger.info(f'Diretório selecionado: {diretorio}')
        return diretorio
    except Exception as e:
        logger.error(f'Erro ao selecionar diretório: {str(e)}')
        return None

@eel.expose
def processar_vsm(dir1, dir2, dir3):
    """Processa análise VSM com validação e tratamento de erros"""
    try:
        # Validação dos diretórios
        for i, dir_path in enumerate([dir1, dir2, dir3], 1):
            if not dir_path or not os.path.isdir(dir_path):
                raise ValueError(f"Diretório {i} inválido ou não selecionado")
        
        logger.info(f'Iniciando processamento VSM | Dir1: {dir1} | Dir2: {dir2} | Dir3: {dir3}')
        
        # Processamento principal
        resultado = GMAG.VSM(dir1, dir2, dir3)
        
        msg = "Análise VSM concluída com sucesso"
        logger.info(msg)
        return {
            'success': True,
            'message': msg,
            'result': str(resultado),
            'timestamp': datetime.now().isoformat(),
            'output_dirs': [dir1, dir2, dir3]
        }
    except Exception as e:
        error_msg = f"Erro no processamento VSM: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'error_details': str(e),
            'timestamp': datetime.now().isoformat()
        }
@eel.expose
def processar_fmr(caminho_arquivo, diretorio_destino, parametros_iniciais=None):
    """
    Processa análise FMR completa com interface gráfica
    
    Args:
        caminho_arquivo (str): Caminho do arquivo de dados
        diretorio_destino (str): Diretório para salvar resultados
        parametros_iniciais (dict): Parâmetros iniciais para o primeiro ângulo
        
    Returns:
        dict: Resultados completos da análise
    """
    try:
        # Validação dos inputs
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        os.makedirs(diretorio_destino, exist_ok=True)
        
        # Inicializa o ajustador
        ajustador = AjustadorMultiplosAngulos(caminho_arquivo)
        
        if not ajustador.angulos_disponiveis or len(ajustador.angulos_disponiveis) == 0:
            raise ValueError("Nenhum ângulo encontrado nos dados")
        
        # Ordena os ângulos
        angulos_ordenados = np.sort(ajustador.angulos_disponiveis)
        
        # Estrutura para armazenar resultados
        resultados = {
            'angulos': [],
            'parametros': [],
            'graficos_angulo': [],
            'grafico_variacao': None,
            'grafico_comparacao': None,
            'arquivos_gerados': [],
            'relatorio_path': None
        }
        
        # Processamento do primeiro ângulo
        primeiro_angulo = angulos_ordenados[0]
        logger.info(f"Processando primeiro ângulo ({primeiro_angulo})")
        
        # Usa parâmetros padrão se não fornecidos
        if not parametros_iniciais:
            parametros_iniciais = {
                'a': 1, 'b': 0, 'c': 1, 'd': 0.8,
                'Hr1': 1000, 'dH1': 50, 
                'Hr2': 1200, 'dH2': 50
            }
        
        # Ajuste do primeiro ângulo
        resultado = ajustador.ajustar_angulo(primeiro_angulo, parametros_iniciais)
        parametros_anteriores = ajustador.resultados[primeiro_angulo]['parametros']
        
        # Salva gráfico do primeiro ângulo
        fig = ajustador.plotar_angulo(primeiro_angulo, mostrar=False)
        nome_arquivo = f"ajuste_angulo_{primeiro_angulo}.png"
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        fig.savefig(caminho_completo)
        plt.close(fig)
        
        # Armazena resultados
        resultados['angulos'].append(primeiro_angulo)
        resultados['parametros'].append(parametros_anteriores)
        resultados['graficos_angulo'].append(caminho_completo)
        resultados['arquivos_gerados'].append(caminho_completo)
        
        # Processamento automático dos demais ângulos
        for angulo in angulos_ordenados[1:]:
            logger.info(f"Processando ângulo {angulo} automaticamente")
            
            resultado = ajustador.ajustar_angulo(angulo, parametros_anteriores)
            parametros_anteriores = ajustador.resultados[angulo]['parametros']
            
            # Salva gráfico do ângulo
            fig = ajustador.plotar_angulo(angulo, mostrar=False)
            nome_arquivo = f"ajuste_angulo_{angulo}.png"
            caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
            fig.savefig(caminho_completo)
            plt.close(fig)
            
            # Armazena resultados
            resultados['angulos'].append(angulo)
            resultados['parametros'].append(parametros_anteriores)
            resultados['graficos_angulo'].append(caminho_completo)
            resultados['arquivos_gerados'].append(caminho_completo)
        
        # Gera gráfico de variação dos parâmetros
        fig = plt.figure(figsize=(15, 10))
        
        # Prepara dados para plotagem
        angulos = resultados['angulos']
        parametros = resultados['parametros']
        
        # Extrai parâmetros de interesse
        Hr1 = [p['Hr1'] for p in parametros]
        Hr2 = [p['Hr2'] for p in parametros]
        dH1 = [p['dH1'] for p in parametros]
        dH2 = [p['dH2'] for p in parametros]
        amp1 = [p['c'] for p in parametros]
        amp2 = [p['d'] for p in parametros]
        
        # Plot dos parâmetros
        plt.subplot(2, 2, 1)
        plt.plot(angulos, Hr1, 'bo-', label='Pico 1')
        plt.plot(angulos, Hr2, 'ro-', label='Pico 2')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Campo de ressonância (Oe)')
        plt.title('Posições dos picos')
        plt.legend()
        plt.grid(True)
        
        plt.subplot(2, 2, 2)
        plt.plot(angulos, dH1, 'bo-', label='Pico 1')
        plt.plot(angulos, dH2, 'ro-', label='Pico 2')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Largura do pico (Oe)')
        plt.title('Larguras dos picos')
        plt.legend()
        plt.grid(True)
        
        plt.subplot(2, 2, 3)
        plt.plot(angulos, amp1, 'bo-', label='Pico 1 (c)')
        plt.plot(angulos, amp2, 'ro-', label='Pico 2 (d)')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Amplitude do pico')
        plt.title('Amplitudes dos picos')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        # Salva o gráfico
        nome_arquivo = "variacao_parametros.png"
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        fig.savefig(caminho_completo)
        plt.close(fig)
        
        resultados['grafico_variacao'] = caminho_completo
        resultados['arquivos_gerados'].append(caminho_completo)
        
        # Gera gráfico de comparação entre ângulos
        fig = ajustador.plotar_comparacao()
        nome_arquivo = "comparacao_angulos.png"
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        fig.savefig(caminho_completo)
        plt.close(fig)
        
        resultados['grafico_comparacao'] = caminho_completo
        resultados['arquivos_gerados'].append(caminho_completo)
        
        # Salva resultados em JSON
        relatorio_path = os.path.join(diretorio_destino, 'resultados_fmr.json')
        with open(relatorio_path, 'w') as f:
            json.dump(resultados, f, indent=2)
        resultados['relatorio_path'] = relatorio_path
        resultados['arquivos_gerados'].append(relatorio_path)
        
        logger.info("Análise FMR concluída com sucesso")
        return {
            'success': True,
            'message': "Análise FMR concluída com sucesso",
            'resultados': resultados
        }
        
    except Exception as e:
        error_msg = f"Erro no processamento FMR: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': error_msg,
            'error_details': str(e)
        }

@eel.expose
def visualizar_grafico(caminho_arquivo):
    """Abre uma visualização do gráfico salvo"""
    try:
        if os.path.exists(caminho_arquivo):
            import webbrowser
            webbrowser.open(caminho_arquivo)
            return True
        return False
    except Exception as e:
        logger.error(f"Erro ao visualizar gráfico: {str(e)}")
        return False


@eel.expose
def salvar_configuracoes(config):
    """Salva configurações do aplicativo"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        # Valida se é JSON válido
        if isinstance(config, str):
            json.loads(config)  # Testa parse
        
        with open(config_path, 'w') as f:
            if isinstance(config, str):
                f.write(config)
            else:
                json.dump(config, f, indent=2)
        
        logger.info('Configurações salvas com sucesso')
        return True
    except Exception as e:
        logger.error(f'Erro ao salvar configurações: {str(e)}')
        return False

@eel.expose
def carregar_configuracoes():
    """Carrega configurações salvas"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info('Configurações carregadas')
                return config
        return None
    except Exception as e:
        logger.error(f'Erro ao carregar configurações: {str(e)}')
        return None

@eel.expose
def get_logs(limit=100):
    """Obtém os últimos logs para exibição na interface"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                lines = f.readlines()[-limit:]
                return ''.join(lines)
        return "Nenhum log disponível"
    except Exception as e:
        return f"Erro ao ler logs: {str(e)}"

# Inicialização segura da aplicação
def main():
    try:
        initialize_eel()
        logger.info("Iniciando aplicativo GMAG")
        
        # Configurações de inicialização
        start_options = {
            'mode': 'chrome',  # ou 'edge', 'default', None
            'host': 'localhost',
            'port': 8080,
            'size': (1280, 800),
            'position': (100, 100),
            'shutdown_delay': 5  # segundos para encerrar
        }
        
        # Tenta usar Chrome, depois Edge, depois o padrão
        try:
            eel.start('index.html', **start_options)
        except EnvironmentError:
            start_options['mode'] = 'edge'
            try:
                eel.start('index.html', **start_options)
            except EnvironmentError:
                start_options['mode'] = None
                eel.start('index.html', **start_options)
                
    except Exception as e:
        logger.critical(f"Falha crítica ao iniciar aplicativo: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
    finally:
        logger.info("Aplicativo GMAG encerrado")

if __name__ == '__main__':
    main()