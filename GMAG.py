import numpy as np, matplotlib.pyplot as plt, os, pandas as pd, scipy.optimize as spy, lmfit

###############################################################
###############################################################
###############################################################
#Todas as funçãoes de "apoio"
gamma = 0.0028 #Variavel global

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

def obter_parametros_iniciais(angulo, parametros_anteriores=None):
    """Obtém parâmetros iniciais do usuário"""
    padroes = {'a': 1, 'b': 1, 'c': 1, 'Hr1': 925, 'dH1': 60}
    
    if parametros_anteriores:
        print(f"\nParâmetros do ajuste anterior disponíveis para ângulo {angulo}:")
        for param, valor in parametros_anteriores.items():
            print(f"{param}: {valor:.4f}")
        
        usar_anteriores = input("Usar esses parâmetros como iniciais? (s/n): ").lower() == 's'
        if usar_anteriores:
            return parametros_anteriores
    
    print(f"\nDigite os parâmetros iniciais para o ângulo {angulo} (Enter para padrão):")
    parametros = {}
    for param in padroes:
        while True:
            try:
                entrada = input(f"{param} (padrão={padroes[param]}): ").strip()
                parametros[param] = float(entrada) if entrada else padroes[param]
                break
            except ValueError:
                print("Por favor digite um número válido")
    return parametros

def trocar_virgula_por_ponto(lista):
    return [item.replace(",", ".") for item in lista]

def plotar_todos_juntos(lista_colA_colB_nome, output_dir=None):
    plt.figure(figsize=(10, 6))
    for colA, colB, nome_do_arquivo in lista_colA_colB_nome:
        if len(colA) == len(colB):
            plt.plot(colA, colB, label=nome_do_arquivo)
        else:
            print(f"Dados inconsistentes em {nome_do_arquivo}")

    plt.xlabel("H(Oe)")
    plt.ylabel("V(mV)")
    plt.legend(loc='best', fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    
    if output_dir:
        output_path = os.path.join(output_dir, "todos_os_graficos.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Gráfico combinado salvo em: {output_path}")

def linear_func(x, a, b):
        return a * x + b

def frequencia_de_ressonancia(x, Hk, Meff):
    return gamma * np.sqrt((x + Hk) * (x + Hk + Meff))  # Corrigido: troquei colchetes por parênteses

def largura_de_linha(dho,alfa):
    return  dho + (alfa / gamma)

def lorentz(x, m, n, Hr, dH):
    """Função Lorentziana assimétrica"""
    parte1 = m * ((dH**2) / (((x - Hr)**2) + (dH**2)))
    parte2 = n * ((dH * (x - Hr)) / (((x - Hr)**2) + (dH**2)))
    return parte1 + parte2

def substituir_virgula_por_espaco(filepath, temp_path):
    """Substitui vírgulas por espaços em arquivo"""
    try:
        with open(filepath, "r") as file:
            data = file.read().replace(",", " ")
        with open(temp_path, "w") as temp_file:
            temp_file.write(data)
        return temp_path
    except Exception as e:
        raise RuntimeError(f"Erro ao processar arquivo {filepath}: {str(e)}")

def encontrar_posicao_mais_proxima_de_zero(vetor, tolerancia=1e-6):
    """
    Encontra a posição (índice) do valor mais próximo de 0 em um vetor com números positivos e negativos.
    
    Parâmetros:
        vetor (list ou np.array): Vetor de números.
        tolerancia (float): Tolerância para considerar valores próximos de 0.
    
    Retorna:
        int: Índice do valor mais próximo de 0.
    """
    if not vetor:
        raise ValueError("O vetor está vazio.")

    # Inicializa o índice do valor mais próximo e a menor distância
    indice_mais_proximo = 0
    menor_distancia = abs(vetor[0])

    # Percorre o vetor
    for i, valor in enumerate(vetor):
        distancia = abs(valor)
        
        # Verifica se o valor atual é mais próximo de 0
        if distancia < menor_distancia - tolerancia:
            indice_mais_proximo = i
            menor_distancia = distancia
        # Se a distância for igual (dentro da tolerância), escolhe o positivo
        elif abs(distancia - menor_distancia) <= tolerancia and valor > 0:
            indice_mais_proximo = i
            menor_distancia = distancia

    return indice_mais_proximo

def remanencia(x,y):
    #valor em y quando x for minimo
    primeira_metade = x[:len(x)//2]
    segunda_metade = x[len(x)//2:]

    posiçãominimo1 = encontrar_posicao_mais_proxima_de_zero(primeira_metade)
    posiçãominimo2 = encontrar_posicao_mais_proxima_de_zero(segunda_metade)
    valor_de_remanencia = (abs(y[posiçãominimo1]) + abs(y[posiçãominimo2])) /2

    return valor_de_remanencia

def coercitividade(x,y):
    #valor em x quando y for 0
    primeira_metade = y[:len(y)//2]
    segunda_metade = y[len(y)//2:]

    posiçãominimo1 = encontrar_posicao_mais_proxima_de_zero(primeira_metade)
    posiçãominimo2 = encontrar_posicao_mais_proxima_de_zero(segunda_metade)

    valor_de_coercitividade = (abs(x[posiçãominimo1]) + abs(x[posiçãominimo2])) /2

    return valor_de_coercitividade

def obter_parametros_iniciais(angulo):
    """Solicita ao usuário os parâmetros iniciais para o ajuste"""
    print(f"\nForneça os parâmetros iniciais para o ângulo {angulo}:")
    
    parametros = {
        'a': float(input("a (offset): ") or 1),
        'b': float(input("b (inclinação): ") or 1),
        'c': float(input("c (amplitude pico 1): ") or 1),
        'd': float(input("d (amplitude pico 2): ") or 1),
        'Hr1': float(input("Hr1 (posição pico 1 em Oe): ") or 1000),
        'dH1': float(input("dH1 (largura pico 1 em Oe): ") or 50),
        'Hr2': float(input("Hr2 (posição pico 2 em Oe): ") or 1200),
        'dH2': float(input("dH2 (largura pico 2 em Oe): ") or 50)
    }
    
    return parametros

###############################################################
###############################################################
###############################################################

def impedancia(diretorio_origem, diretorio_destino):
    """
    Processa arquivos de dados, plota gráficos e ajusta curvas Lorentzianas
    
    Args:
        diretorio_origem (str): Caminho para os arquivos de dados originais
        diretorio_destino (str): Caminho para salvar os gráficos e resultados
    """
    # Verificação de diretórios
    if not os.path.exists(diretorio_origem):
        raise FileNotFoundError(f"Diretório de origem não encontrado: {diretorio_origem}")
    
    os.makedirs(diretorio_destino, exist_ok=True)
    
    # Listas para armazenar os parâmetros
    lista_Hr = []
    lista_dH = []
    nomes_arquivos = []

    # Processamento dos arquivos
    for nome_arquivo in os.listdir(diretorio_origem):
        caminho_origem = os.path.join(diretorio_origem, nome_arquivo)
        
        if not os.path.isfile(caminho_origem):
            print(f"AVISO: {caminho_origem} não é um arquivo válido. Pulando...")
            continue
        
        # Criação de arquivo temporário
        temp_path = os.path.join(diretorio_destino, f"temp_{nome_arquivo}")
        try:
            temp_path = substituir_virgula_por_espaco(caminho_origem, temp_path)
            
            # Carregamento dos dados
            dados = np.loadtxt(temp_path)
            
            if dados.shape[1] < 5:
                print(f"AVISO: Arquivo {nome_arquivo} não tem colunas suficientes. Pulando...")
                continue
            
            x = dados[:, 0]
            y = dados[:, 4]
            
            # Plot dos dados brutos
            plt.figure(figsize=(10, 6))
            plt.plot(x, y, 'b-', linewidth=1)
            plt.xlabel("Campo (Oe)", fontsize=12)
            plt.ylabel("Impedância (Ω)", fontsize=12)
            plt.title(f"Impedância - {os.path.splitext(nome_arquivo)[0]}", fontsize=14)
            plt.grid(True, alpha=0.3)
            
            # Salvar gráfico bruto
            nome_saida = f"{os.path.splitext(nome_arquivo)[0]}_bruto.png"
            caminho_saida = os.path.join(diretorio_destino, nome_saida)
            plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Gráfico bruto salvo: {caminho_saida}")
            
            # Ajuste do modelo - APENAS NA SEGUNDA METADE DOS DADOS
            metade = len(x) // 2 + 1
            x_fit = x[metade:]
            y_fit = y[metade:]
            
            # Estimativas iniciais inteligentes usando apenas a segunda metade
            Hr_guess = x_fit[np.argmax(y_fit)]
            dH_guess = (max(x_fit) - min(x_fit))/10
            m_guess = max(y_fit)
            
            modelo = lmfit.Model(lorentz)
            params = modelo.make_params(
                m=m_guess,
                n=0.0,
                Hr=Hr_guess,
                dH=dH_guess
            )
            
            # Restrições para parâmetros físicos
            params['dH'].min = 0
            params['m'].min = 0
            
            # Faz o fitting apenas com a segunda metade
            resultado = modelo.fit(y_fit, params, x=x_fit)

            # Armazena os valores e nome do arquivo
            lista_Hr.append(resultado.params['Hr'].value)
            lista_dH.append(resultado.params['dH'].value)
            nomes_arquivos.append(os.path.splitext(nome_arquivo)[0])
            
            # Plot do ajuste completo (mostra todos os dados)
            plt.figure(figsize=(10, 6))
            plt.plot(x_fit, y_fit, 'b.', label="Dados experimentais")
            plt.plot(x_fit, resultado.best_fit, 'r-', linewidth=2, 
                    label="Ajuste Lorentziano (2ª metade)")
            plt.xlabel("Campo (Oe)", fontsize=12)
            plt.ylabel("Impedância (Ω)", fontsize=12)
            plt.title(f"Ajuste - {os.path.splitext(nome_arquivo)[0]}", fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Adicionar parâmetros do ajuste ao gráfico
            texto_ajuste = (
                f"Hr = {resultado.params['Hr'].value:.2f} ± {resultado.params['Hr'].stderr:.2f} Oe\n"
                f"dH = {resultado.params['dH'].value:.2f} ± {resultado.params['dH'].stderr:.2f} Oe"
            )
            plt.text(0.02, 0.98, texto_ajuste, transform=plt.gca().transAxes,
                    verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
            
            # Salvar gráfico ajustado
            nome_saida = f"{os.path.splitext(nome_arquivo)[0]}_ajuste.png"
            caminho_saida = os.path.join(diretorio_destino, nome_saida)
            plt.savefig(caminho_saida, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Gráfico com ajuste salvo: {caminho_saida}")
            
            # Salvar parâmetros do ajuste em arquivo
            nome_relatorio = f"{os.path.splitext(nome_arquivo)[0]}_parametros.txt"
            caminho_relatorio = os.path.join(diretorio_destino, nome_relatorio)
            with open(caminho_relatorio, 'w') as f:
                f.write(resultado.fit_report())
            print(f"Relatório de ajuste salvo: {caminho_relatorio}")

        except Exception as e:
            print(f"ERRO ao processar {nome_arquivo}: {str(e)}")
        finally:
            # Limpeza do arquivo temporário
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"AVISO: Não foi possível remover arquivo temporário {temp_path}: {str(e)}")

    # Plot dos resultados após processar todos os arquivos
    if lista_Hr and lista_dH:
        # Criar array de frequências correspondente ao número de amostras
        num_amostras = len(lista_Hr)
        frequencias = np.linspace(1001, 1001 + (num_amostras-1)*10, num_amostras)
        frequencias_ghz = np.array(frequencias) / 1000
        
        print(f"\nNúmero de amostras: {num_amostras}")
        print(f"Faixa de frequências ajustada: {frequencias[0]} a {frequencias[-1]} MHz")

        # --- AJUSTE PARA FREQUÊNCIA DE RESSONÂNCIA ---
        modelo_freq = lmfit.Model(frequencia_de_ressonancia)
        params_freq = modelo_freq.make_params(Hk=100, Meff=1000)
        params_freq['Hk'].min = 0
        params_freq['Meff'].min = 0
        
        try:
            # Ajuste invertido (Hr vs frequência)
            resultado_freq = modelo_freq.fit(frequencias_ghz, params_freq, x=np.array(lista_Hr))
            
            # Gráfico para Hr vs Frequência com ajuste
            plt.figure(figsize=(12, 6))
            plt.plot(lista_Hr, frequencias_ghz, 'bo', markersize=6, label='Dados experimentais')
            
            # Curva ajustada
            x_fit = np.linspace(min(lista_Hr), max(lista_Hr), 100)
            plt.plot(x_fit, modelo_freq.eval(resultado_freq.params, x=x_fit), 
                    'r-', label='Ajuste teórico')
            
            plt.xlabel('Campo de Ressonância (Oe)', fontsize=12)
            plt.ylabel('Frequência (GHz)', fontsize=12)
            plt.title('Frequência de Ressonância vs Campo', fontsize=14)
            
            # Adicionar parâmetros do ajuste
            texto_ajuste = (
                f"Hk = {resultado_freq.params['Hk'].value:.2f} ± {resultado_freq.params['Hk'].stderr:.2f} Oe\n"
                f"Meff = {resultado_freq.params['Meff'].value:.2f} ± {resultado_freq.params['Meff'].stderr:.2f} Oe"
            )
            plt.text(0.02, 0.98, texto_ajuste, transform=plt.gca().transAxes,
                    verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
            
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            caminho_saida_freq = os.path.join(diretorio_destino, 'frequencia_ressonancia_ajuste.png')
            plt.savefig(caminho_saida_freq, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Gráfico Frequência de Ressonância salvo: {caminho_saida_freq}")
            
            # Salvar parâmetros do ajuste
            with open(os.path.join(diretorio_destino, 'parametros_frequencia.txt'), 'w') as f:
                f.write(resultado_freq.fit_report())
            
        except Exception as e:
            print(f"ERRO no ajuste da frequência de ressonância: {str(e)}")
        
        # --- AJUSTE PARA LARGURA DE LINHA ---
        def largura_linha_model(x, dho, alfa):
            return dho + (alfa * x)  # x já está em GHz, então alfa = α/γ
        
        modelo_largura = lmfit.Model(largura_linha_model)
        params_largura = modelo_largura.make_params(
            dho=np.mean(lista_dH)/2,  # Valor inicial mais seguro
            alfa=0.1
        )
        params_largura['dho'].min = 0
        params_largura['alfa'].min = 0
        
        try:
            resultado_largura = modelo_largura.fit(lista_dH, params_largura, x=frequencias_ghz)
            
            # Verifica se o ajuste foi bem-sucedido
            if resultado_largura is not None:
                # Gráfico para dH vs Frequência com ajuste
                plt.figure(figsize=(12, 6))
                plt.plot(frequencias_ghz, lista_dH, 'ro', markersize=6, label='Dados experimentais')
                
                # Curva ajustada
                x_fit = np.linspace(min(frequencias_ghz), max(frequencias_ghz), 100)
                y_fit = modelo_largura.eval(resultado_largura.params, x=x_fit)
                plt.plot(x_fit, y_fit, 'b-', 
                        label=f'Ajuste: ΔH = {resultado_largura.params["dho"].value:.2f} + {resultado_largura.params["alfa"].value:.4f}·f')
                
                plt.xlabel('Frequência (GHz)', fontsize=12)
                plt.ylabel('Largura de Linha (Oe)', fontsize=12)
                plt.title('Largura de Linha vs Frequência', fontsize=14)
                
                # Adicionar parâmetros do ajuste (com verificação de erros)
                texto_ajuste = []
                if resultado_largura.params['dho'].stderr is not None:
                    texto_ajuste.append(f"ΔH₀ = {resultado_largura.params['dho'].value:.2f} ± {resultado_largura.params['dho'].stderr:.2f} Oe")
                else:
                    texto_ajuste.append(f"ΔH₀ = {resultado_largura.params['dho'].value:.2f} Oe (erro não disponível)")
                
                if resultado_largura.params['alfa'].stderr is not None:
                    texto_ajuste.append(f"α/γ = {resultado_largura.params['alfa'].value:.4f} ± {resultado_largura.params['alfa'].stderr:.4f}")
                else:
                    texto_ajuste.append(f"α/γ = {resultado_largura.params['alfa'].value:.4f} (erro não disponível)")
                
                texto_ajuste.append(f"α = {resultado_largura.params['alfa'].value * gamma:.4f} (α = (α/γ)×γ)")
                
                plt.text(0.02, 0.98, "\n".join(texto_ajuste), transform=plt.gca().transAxes,
                        verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8))
                
                plt.grid(True, alpha=0.3)
                plt.legend()
                plt.tight_layout()
                
                caminho_saida_largura = os.path.join(diretorio_destino, 'largura_linha_ajuste.png')
                plt.savefig(caminho_saida_largura, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"Gráfico Largura de Linha salvo: {caminho_saida_largura}")
                
                # Salvar parâmetros do ajuste
                with open(os.path.join(diretorio_destino, 'parametros_largura.txt'), 'w') as f:
                    f.write(resultado_largura.fit_report())
            else:
                print("AVISO: O ajuste da largura de linha retornou None")
                
        except Exception as e:
            print(f"ERRO no ajuste da largura de linha: {str(e)}")
            # Plot dos dados sem ajuste
            plt.figure(figsize=(12, 6))
            plt.plot(frequencias_ghz, lista_dH, 'ro', markersize=6, label='Dados experimentais')
            plt.xlabel('Frequência (GHz)', fontsize=12)
            plt.ylabel('Largura de Linha (Oe)', fontsize=12)
            plt.title('Largura de Linha vs Frequência (ajuste falhou)', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            caminho_saida_largura = os.path.join(diretorio_destino, 'largura_linha_sem_ajuste.png')
            plt.savefig(caminho_saida_largura, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Gráfico sem ajuste salvo: {caminho_saida_largura}")
            
            # Salvar parâmetros do ajuste
            with open(os.path.join(diretorio_destino, 'parametros_largura.txt'), 'w') as f:
                f.write(resultado_largura.fit_report())
            
        except Exception as e:
            print(f"ERRO no ajuste da largura de linha: {str(e)}")

###############################################################
###############################################################
###############################################################

def VSM(diretorio_origem, diretorio_caminho, diretorio_destino):
    # Verifica se o diretório de destino existe; se não, cria
    if not os.path.exists(diretorio_destino):
        os.makedirs(diretorio_destino)

    # Lista os arquivos no diretório de origem
    arquivos = os.listdir(diretorio_origem)
    Valorderemanencia = []
    Valordecoercitividade = []

    # Processa cada arquivo no diretório de origem
    for nome_da_amostra in arquivos:
        caminho_origem = os.path.join(diretorio_origem, nome_da_amostra)
        
        if os.path.isfile(caminho_origem):
            with open(caminho_origem, "r") as arquivo_origem:
                conteudo = arquivo_origem.read()

                # Modifica o conteúdo
                indice = conteudo.find("(emu)")
                if indice != -1:
                    conteudo = conteudo[indice+5:]
                else:
                    print(f"AVISO: '(emu)' não encontrado no arquivo {nome_da_amostra}")
                    continue  # Pula para o próximo arquivo

                # Salva o conteúdo modificado em um novo arquivo
                novo_nome = f"arquivo_de_modificação_{nome_da_amostra}"
                caminho_do_meio = os.path.join(diretorio_caminho, novo_nome)
                with open(caminho_do_meio, "w") as arquivo_destino:
                    arquivo_destino.write(conteudo)

    # Processa os arquivos modificados
    arquivos_modificados = os.listdir(diretorio_caminho)
    for nome_do_arquivo in arquivos_modificados:
        colunaA = []
        colunaB = []
        caminho_do_meio = os.path.join(diretorio_caminho, nome_do_arquivo)

        if os.path.isfile(caminho_do_meio):
            with open(caminho_do_meio, "r") as arquivo:
                linhas = arquivo.readlines()

                for linha in linhas:
                    elementos = linha.split()
                    if len(elementos) >= 2:
                        colunaA.append(elementos[0])
                        colunaB.append(elementos[1])

                # Converte os dados para float
                colA = list(map(float, colunaA))
                colB = list(map(float, colunaB))

                # Verifica se há dados válidos
                if len(colB) == 0:
                    print(f"AVISO: Nenhum dado válido no arquivo {nome_do_arquivo}")
                    continue

                # Normaliza os dados
                nao_sei_oq_vai_sair = [(2*y - (max(colB) + min(colB))) / (max(colB) - min(colB)) for y in colB]
                Valorderemanencia.append(remanencia(colA,nao_sei_oq_vai_sair))
                Valordecoercitividade.append(coercitividade(colA,nao_sei_oq_vai_sair))

                # Plota e salva o gráfico
                plt.plot(colA, nao_sei_oq_vai_sair)
                plt.xlabel("Field (Oe)")
                plt.ylabel("ARB units")
                plt.text(
                    x=0.98,  # Posição x (98% da largura do gráfico, próximo à borda direita)
                    y=0.02,  # Posição y (2% da altura do gráfico, próximo à borda inferior)
                    s=nome_do_arquivo,  # Texto
                    fontsize=12,  # Tamanho da fonte
                    color="black",  # Cor do texto
                    transform=plt.gca().transAxes,  # Usar coordenadas relativas ao gráfico
                    horizontalalignment="right",  # Alinhamento horizontal (direita)
                    verticalalignment="bottom"  # Alinhamento vertical (inferior)
                )
                plt.grid(True)
                nome_do_grafico = os.path.join(diretorio_destino, f"grafico_{nome_do_arquivo}.png")
                plt.savefig(nome_do_grafico)
                plt.close()

    vetor = np.linspace(0, 180, 19)
    plt.plot(vetor,Valorderemanencia)
    plt.xlabel("Angulos")
    plt.ylabel("ARB units")
    plt.grid(True)
    nome_do_grafico = os.path.join(diretorio_destino, f"Remanencia.png")
    plt.savefig(nome_do_grafico)
    plt.close()

    plt.plot(vetor,Valordecoercitividade)
    plt.xlabel("Angulos")
    plt.ylabel("ARB units")
    plt.grid(True)
    nome_do_grafico = os.path.join(diretorio_destino, f"Coercitividade.png")
    plt.savefig(nome_do_grafico)
    plt.close()

    return "Tudo feito"

###############################################################
###############################################################
###############################################################

def Resistencia(arquivos_no_diretorio, Diretorio_inicial):

    arquivos_no_diretorio = os.listdir(Diretorio_inicial)
    
    for indice, nome_do_arquivo in enumerate(arquivos_no_diretorio):
        #Neste ponto eu tenho o nome dos arquivos no estado bruto, na variavel nome_dos_arquivos
        #preciso mudar o nome dele para nome_novo.txt
        ColunaA, ColunaB = [], []
        
        caminho_a_ser_seguido = os.path.join(Diretorio_inicial,nome_do_arquivo)

        if os.path.isfile(caminho_a_ser_seguido):
            with open(caminho_a_ser_seguido, "r") as arquivo:
                # Ler todas as linhas do arquivo
                linhas = arquivo.readlines()
                
                # Iterar sobre cada linha do arquivo
                for linha in linhas:
                    # Dividir a linha em elementos usando o separador apropriado
                    elementos = linha.split()  # Supondo que os elementos estejam separados por espaço em branco

                    # Verificar se há pelo menos dois elementos na linha
                    if len(elementos) >= 2:
                        # Adicionar os elementos correspondentes a cada coluna
                        ColunaA.append(elementos[0])
                        ColunaB.append(elementos[1])
                    

                colA = list(map(float, ColunaA))
                colB = list(map(float, ColunaB))
            nome_grafico = f"{nome_do_arquivo}_{indice}.png"

            plt.plot(colA,colB)
            plt.xlabel("H(Oe)")
            plt.ylabel("dR")
            plt.grid(True)
            plt.savefig(f'c:\\Users\\Gabriel\\Desktop\\Backup jamyk\\Py(t)_Jamykson\\teste\\{nome_grafico}')
            plt.close()

###############################################################
###############################################################
###############################################################

def DRX(arquivo):
    # Comprimento de onda da radiação X (exemplo para Cu-Kα)
    l = 1.54056  

    # Lendo o arquivo
    J = pd.read_table(arquivo, names=['K', 'L'], sep=',')
    
    # Extraindo os dados
    x = J['K']
    y = J['L']

    # Plotando o gráfico para seleção manual de picos
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, label="Sinal", color='red')
    plt.xlabel("Ângulo (°)")
    plt.ylabel("Intensidade")
    plt.title("Clique nos picos desejados e pressione Enter")
    pontos_selecionados = plt.ginput(n=-1, timeout=0)
    plt.close()

    # Extraindo os valores de ângulo selecionados
    angulos = np.array([p[0] for p in pontos_selecionados])
    print("Ângulos selecionados:", angulos)

    # Convertendo ângulos para qf (com correção na equação)
    qf = (4 * np.pi * np.sin(np.radians(angulos / 2))) / l

    # Criando índices para ajuste
    indices = np.arange(len(angulos))

    # Ajuste de curva
    params, _ = spy.curve_fit(linear_func, indices, qf)
    a, b = params

    # Cálculo da espessura e taxa de crescimento
    espessura = 2 * np.pi / a
    tempo = 300  # Tempo fixo (em segundos)
    taxa = espessura / tempo

    print(f"Espessura: {espessura:.4f} nm")
    print(f"Taxa de crescimento: {taxa:.4f} nm/s")

    # Plotando os resultados do ajuste
    x_fit = np.linspace(0, len(angulos) - 1, 100)
    y_fit = linear_func(x_fit, a, b)

    plt.figure(figsize=(8, 5))
    plt.scatter(indices, qf, color='red', label='Pontos Selecionados')
    plt.plot(x_fit, y_fit, label='Ajuste Linear', linestyle='--', color='blue')
    plt.xlabel("Índice")
    plt.ylabel("qf (1/nm)")
    plt.title("Ajuste Linear de qf")
    plt.legend()
    plt.grid()
    plt.show()
    return "Tudo Pronto"

###############################################################
###############################################################
###############################################################

def Eletroima(Diretorio_inicial, Diretorio_final):
    arquivos_no_diretorio = os.listdir(Diretorio_inicial)

    # Criar diretório de saída se não existir
    os.makedirs(Diretorio_final, exist_ok=True)

    # Lista para armazenar os dados de todos os arquivos
    todos_os_dados = []

    for indice, nome_do_arquivo in enumerate(arquivos_no_diretorio):
        caminho_arquivo = os.path.join(Diretorio_inicial, nome_do_arquivo)

        with open(caminho_arquivo, "r", errors="ignore") as f:
            linhas = f.readlines()

        ColunaA, ColunaB = [], []

        for linha in linhas:
            elementos = linha.split()
            if len(elementos) >= 2:
                ColunaA.append(elementos[0])
                ColunaB.append(elementos[1])

        # Trocar vírgulas por pontos
        ColunaA = trocar_virgula_por_ponto(ColunaA)
        ColunaB = trocar_virgula_por_ponto(ColunaB)

        try:
            colA = list(map(float, ColunaA))
            colB = list(map(float, ColunaB))
            media = np.mean(colB)
            colB = [y - media for y in colB]


        except ValueError:
            print(f"Erro ao converter os dados do arquivo: {nome_do_arquivo}")
            continue

        # Guardar os dados para o gráfico conjunto
        todos_os_dados.append((colA, colB, nome_do_arquivo))

        # Plotar gráfico individual
        plt.figure()
        plt.plot(colA, colB)
        plt.xlabel("H(Oe)")
        plt.ylabel("V(mV)")
        plt.title("Gráfico individual")
        plt.grid(True)

        # Adicionar nome do arquivo no canto superior direito
        plt.text(
            x=max(colA),
            y=max(colB),
            s=nome_do_arquivo,
            fontsize=9,
            ha='right',
            va='top',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray')
        )

        # Salvar gráfico individual
        Caminho_de_saida = os.path.join(Diretorio_final, f"grafico_{nome_do_arquivo}.png")
        plt.savefig(Caminho_de_saida, dpi=300, bbox_inches='tight')
        print(f"Gráfico salvo: {Caminho_de_saida}")

    # Plotar todos os gráficos juntos
    plotar_todos_juntos(todos_os_dados,Diretorio_final)

###############################################################
###############################################################
###############################################################

def FMR(caminho_arquivo, diretorio_destino):
    
    if not os.path.exists(caminho_arquivo):
        print(f"Erro: Arquivo não encontrado em {caminho_arquivo}")
        return

    try:
        # Criar diretório de destino se não existir
        os.makedirs(diretorio_destino, exist_ok=True)
        
        ajustador = AjustadorMultiplosAngulos(caminho_arquivo)
        
        if ajustador.angulos_disponiveis is None or len(ajustador.angulos_disponiveis) == 0:
            print("Nenhum ângulo encontrado nos dados")
            return
        
        # Ordena os ângulos
        angulos_ordenados = np.sort(ajustador.angulos_disponiveis)
        parametros_anteriores = None
        
        # Listas para armazenar resultados de ambos os picos
        angulos_plot = []
        Hr1_plot = []
        dH1_plot = []
        Hr2_plot = []
        dH2_plot = []
        amplitude1_plot = []  # Para o parâmetro c
        amplitude2_plot = []  # Para o parâmetro d
        
         # Loop especial para o primeiro ângulo (0°)
        primeiro_angulo = angulos_ordenados[0]
        while True:
            print(f"\n=== Processando ângulo {primeiro_angulo} ===")
            
            # Opções para o usuário
            if parametros_anteriores:
                print("\nOpções:")
                print("1 - Usar parâmetros do ajuste anterior como iniciais")
                print("2 - Fornecer novos parâmetros iniciais")
                print("3 - Finalizar ajuste e prosseguir")
                
                opcao = input("Escolha uma opção (1/2/3): ").strip()
                
                if opcao == '1':
                    parametros = parametros_anteriores
                elif opcao == '2':
                    parametros = obter_parametros_iniciais(primeiro_angulo)
                elif opcao == '3':
                    break
                elif opcao == '4':
                    exit()
                else:
                    print("Opção inválida, tente novamente")
                    continue
            else:
                parametros = obter_parametros_iniciais(primeiro_angulo)
            
            # Realiza o ajuste
            resultado = ajustador.ajustar_angulo(primeiro_angulo, parametros)
            print("\nResultados do ajuste:")
            lmfit.report_fit(resultado.params)
            
            # Armazena parâmetros
            parametros_anteriores = ajustador.resultados[primeiro_angulo]['parametros']
            
            # Adiciona aos dados de plotagem
            angulos_plot.append(primeiro_angulo)
            Hr1_plot.append(parametros_anteriores['Hr1'])
            dH1_plot.append(parametros_anteriores['dH1'])
            Hr2_plot.append(parametros_anteriores['Hr2'])
            dH2_plot.append(parametros_anteriores['dH2'])
            
            # Plota os resultados interativamente
            print("\nExibindo gráfico do ajuste (feche para continuar)...")
            fig = ajustador.plotar_angulo(primeiro_angulo, mostrar=True)  # Mostra interativamente
            
            # Salva os resultados
            nome_arquivo = f"ajuste_angulo_{primeiro_angulo}.png"
            caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
            fig.savefig(caminho_completo)
            plt.close(fig)
            print(f"Gráfico salvo em: {caminho_completo}")            
        
        # Processa os demais ângulos automaticamente
        for angulo in angulos_ordenados[1:]:
            print(f"\n=== Processando ângulo {angulo} (automático) ===")
            
            # Usa os parâmetros do ângulo anterior como iniciais
            resultado = ajustador.ajustar_angulo(angulo, parametros_anteriores)
            print("\nResultados do ajuste:")
            lmfit.report_fit(resultado.params)
            
            # Atualiza parâmetros para o próximo ângulo
            parametros_anteriores = ajustador.resultados[angulo]['parametros']
            
            # Adiciona aos dados de plotagem para ambos picos
            angulos_plot.append(angulo)
            Hr1_plot.append(parametros_anteriores['Hr1'])
            dH1_plot.append(parametros_anteriores['dH1'])
            Hr2_plot.append(parametros_anteriores['Hr2'])
            dH2_plot.append(parametros_anteriores['dH2'])
            amplitude1_plot.append(parametros_anteriores['c'])
            amplitude2_plot.append(parametros_anteriores['d'])
            
            # Plota e salva os resultados
            fig = ajustador.plotar_angulo(angulo, mostrar=False)
            nome_arquivo = f"ajuste_angulo_{angulo}.png"
            caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
            fig.savefig(caminho_completo)
            plt.close(fig)
            print(f"Gráfico salvo em: {caminho_completo}")
        
        # Plot dos parâmetros em função do ângulo
        plt.figure(figsize=(15, 10))
        
        # Subplot para posições dos picos (Hr1 e Hr2)
        plt.subplot(2, 2, 1)
        plt.plot(angulos_plot, Hr1_plot, 'bo-', label='Pico 1')
        plt.plot(angulos_plot, Hr2_plot, 'ro-', label='Pico 2')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Campo de ressonância (Oe)')
        plt.title('Variação das posições dos picos com o ângulo')
        plt.legend()
        plt.grid(True)
        
        # Subplot para larguras dos picos (dH1 e dH2)
        plt.subplot(2, 2, 2)
        plt.plot(angulos_plot, dH1_plot, 'bo-', label='Pico 1')
        plt.plot(angulos_plot, dH2_plot, 'ro-', label='Pico 2')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Largura do pico (Oe)')
        plt.title('Variação das larguras dos picos com o ângulo')
        plt.legend()
        plt.grid(True)
        
        # Subplot para amplitudes dos picos (c e d)
        plt.subplot(2, 2, 3)
        plt.plot(angulos_plot, amplitude1_plot, 'bo-', label='Pico 1 (c)')
        plt.plot(angulos_plot, amplitude2_plot, 'ro-', label='Pico 2 (d)')
        plt.xlabel('Ângulo (graus)')
        plt.ylabel('Amplitude do pico')
        plt.title('Variação das amplitudes dos picos com o ângulo')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        # Salva o gráfico de variação dos parâmetros
        nome_arquivo = "variacao_parametros.png"
        caminho_completo = os.path.join(diretorio_destino, nome_arquivo)
        plt.savefig(caminho_completo)
        print(f"Gráfico de variação dos parâmetros salvo em: {caminho_completo}")
        
        plt.show()
            
    except Exception as e:
        print(f"\nOcorreu um erro: {str(e)}")

    return "Tudo Pronto"
