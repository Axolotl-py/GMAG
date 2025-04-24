import eel
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import sys
from datetime import datetime
import GMAG  # Sua biblioteca GMAG

# Configurações
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.gmag_config.json')
LOG_FILE = os.path.join(os.path.expanduser('~'), 'gmag_process.log')

def log_processamento(mensagem):
    """Registra mensagens no arquivo de log"""
    with open(LOG_FILE, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {mensagem}\n")

def carregar_configuracao():
    """Carrega a configuração do arquivo"""
    config_padrao = {
        'input_dir': '',
        'output_dir': '',
        'historico': [],
        'configuracoes': {
            'tema': 'escuro',
            'ultimo_modo': None
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Migração para versões mais novas
                if 'configuracoes' not in config:
                    config['configuracoes'] = config_padrao['configuracoes']
                return {**config_padrao, **config}
    except Exception as e:
        log_processamento(f"Erro ao carregar configuração: {str(e)}")
        messagebox.showerror("Erro", f"Não foi possível carregar as configurações: {str(e)}")
    
    return config_padrao

def salvar_configuracao(config):
    """Salva a configuração no arquivo"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        log_processamento(f"Erro ao salvar configuração: {str(e)}")
        messagebox.showerror("Erro", f"Não foi possível salvar as configurações: {str(e)}")
        return False

@eel.expose  # Esta linha é ESSENCIAL
def executar_processamento():
    """Função que será chamada pelo JavaScript"""
    # Sua lógica de processamento aqui
    return {"status": "success", "message": "Processamento concluído"}

@eel.expose
def selecionar_diretorio(tipo='input'):
    """Abre diálogo para selecionar diretório"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        
        caminho = filedialog.askdirectory(
            title=f"Selecione o diretório de {'entrada' if tipo == 'input' else 'saída'}",
            mustexist=True
        )
        
        if caminho:
            config = carregar_configuracao()
            config[f'{tipo}_dir'] = caminho
            salvar_configuracao(config)
            log_processamento(f"Diretório {tipo} selecionado: {caminho}")
            return {'status': 'success', 'caminho': caminho}
        
        return {'status': 'cancelled'}
    except Exception as e:
        log_processamento(f"Erro ao selecionar diretório {tipo}: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def obter_configuracoes():
    """Retorna todas as configurações"""
    config = carregar_configuracao()
    return {
        'diretorios': {
            'input_dir': config.get('input_dir', ''),
            'output_dir': config.get('output_dir', '')
        },
        'tema': config['configuracoes'].get('tema', 'escuro'),
        'ultimo_modo': config['configuracoes'].get('ultimo_modo')
    }

@eel.expose
def salvar_configuracoes(novas_config):
    """Salva novas configurações"""
    try:
        config = carregar_configuracao()
        if 'tema' in novas_config:
            config['configuracoes']['tema'] = novas_config['tema']
        if 'ultimo_modo' in novas_config:
            config['configuracoes']['ultimo_modo'] = novas_config['ultimo_modo']
        salvar_configuracao(config)
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@eel.expose
def validar_diretorios():
    """Valida se os diretórios existem e são acessíveis"""
    config = carregar_configuracao()
    resultados = {}
    
    for tipo in ['input', 'output']:
        caminho = config.get(f'{tipo}_dir', '')
        if not caminho:
            resultados[tipo] = {'valido': False, 'erro': 'Diretório não configurado'}
            continue
        
        try:
            if not os.path.isdir(caminho):
                resultados[tipo] = {'valido': False, 'erro': 'Diretório não existe'}
            elif not os.access(caminho, os.R_OK if tipo == 'input' else os.W_OK):
                resultados[tipo] = {'valido': False, 'erro': 'Permissão negada'}
            else:
                resultados[tipo] = {'valido': True, 'caminho': caminho}
        except Exception as e:
            resultados[tipo] = {'valido': False, 'erro': str(e)}
    
    return resultados

@eel.expose
def executar_processamento_especifico(modo):
    """Executa o processamento específico conforme o modo selecionado"""
    try:
        config = carregar_configuracao()
        input_dir = config.get('input_dir', '')
        output_dir = config.get('output_dir', '')
        
        if not input_dir or not output_dir:
            return {'status': 'error', 'message': 'Diretórios não configurados'}
        
        # Registrar início do processamento
        inicio = datetime.now()
        log_processamento(f"Iniciando processamento {modo} - Entrada: {input_dir}, Saída: {output_dir}")
        
        # Chamar a função específica da biblioteca GMAG
        funcoes = {
            'DRX': GMAG.DRX,
            'VSM': GMAG.VSM,
            'Termoeletrico': GMAG.trocar_virgula_por_ponto,
            'MagnetoImpedancia': GMAG.impedancia,
            'FMR': GMAG.FMR,
            'Eletroima': GMAG.Eletroima,
            'Resistencia': GMAG.Resistencia
        }
        
        if modo not in funcoes:
            return {'status': 'error', 'message': 'Modo de operação inválido'}
        
        resultado = funcoes[modo](input_dir, output_dir)
        
        # Registrar conclusão
        duracao = (datetime.now() - inicio).total_seconds()
        entrada_processamento = {
            'modo': modo,
            'input': input_dir,
            'output': output_dir,
            'data': inicio.strftime('%Y-%m-%d %H:%M:%S'),
            'duracao': duracao,
            'resultado': str(resultado)
        }
        
        config['historico'].insert(0, entrada_processamento)
        config['configuracoes']['ultimo_modo'] = modo
        salvar_configuracao(config)
        
        log_processamento(f"Processamento {modo} concluído em {duracao:.2f} segundos")
        return {
            'status': 'success',
            'resultado': str(resultado),
            'duracao': duracao,
            'processamento': entrada_processamento
        }
        
    except Exception as e:
        log_processamento(f"Erro durante o processamento {modo}: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@eel.expose
def obter_historico(limite=10):
    """Retorna o histórico de processamentos"""
    config = carregar_configuracao()
    return config.get('historico', [])[:limite]

@eel.expose
def limpar_historico():
    """Limpa o histórico de processamentos"""
    try:
        config = carregar_configuracao()
        config['historico'] = []
        salvar_configuracao(config)
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    try:
        # Verificar e criar arquivo de log se necessário
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, 'w').close()
        
        log_processamento("Iniciando aplicativo GMAG")
        
        eel.init('web')
        eel.start(
            'index.html',
            size=(1280, 800),
            mode='chrome',
            host='localhost',
            port=8080,
            cmdline_args=['--disable-http-cache']
        )
    except Exception as e:
        log_processamento(f"Falha crítica ao iniciar aplicativo: {str(e)}")
        messagebox.showerror("Erro Fatal", f"Não foi possível iniciar o aplicativo: {str(e)}")
        sys.exit(1)