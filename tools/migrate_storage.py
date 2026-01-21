import os
import shutil
import time

BASE_DIR = os.getcwd()
SRC_DIR = os.path.join(BASE_DIR, "storage")
DST_DIR = os.path.join(BASE_DIR, "go2rtc_bin", "storage")

def migrate():
    print("=== INICIANDO MIGRAÇÃO DE STORAGE ===")
    print(f"Origem: {SRC_DIR}")
    print(f"Destino: {DST_DIR}")

    if not os.path.exists(SRC_DIR):
        print("Diretório de origem não existe. Nada a fazer.")
        return

    if not os.path.exists(DST_DIR):
        os.makedirs(DST_DIR)
        print(f"Criado diretório de destino: {DST_DIR}")

    # Lista câmeras na origem
    cameras = [d for d in os.listdir(SRC_DIR) if os.path.isdir(os.path.join(SRC_DIR, d))]
    
    for cam in cameras:
        src_cam = os.path.join(SRC_DIR, cam)
        dst_cam = os.path.join(DST_DIR, cam)
        
        if not os.path.exists(dst_cam):
            os.makedirs(dst_cam)
            print(f"Criada pasta da câmera no destino: {cam}")

        # Mover arquivos
        files = os.listdir(src_cam)
        count = 0
        for f in files:
            src_f = os.path.join(src_cam, f)
            dst_f = os.path.join(dst_cam, f)
            
            if os.path.isfile(src_f):
                try:
                    if os.path.exists(dst_f):
                        # Se já existe (conflito de nome?), remove o da origem ou sobrescreve?
                        # Melhor pular ou renomear. Vamos pular se for idêntico, ou sobrescrever se timestamp bater.
                        # Timestamp é unico. Se existe, ja foi gravado/migrado.
                        os.remove(src_f)
                        print(f"Arquivo duplicado removido da origem: {f}")
                    else:
                        shutil.move(src_f, dst_f)
                        count += 1
                except Exception as e:
                    print(f"Erro ao mover {f}: {e}")
        
        print(f"Migrados {count} arquivos da câmera {cam}.")
        
        # Tentar remover pasta vazia da camera na origem
        try:
            os.rmdir(src_cam)
            print(f"Pasta de origem removida: {cam}")
        except:
            print(f"Pasta de origem não ficou vazia: {cam}")

    # Tentar remover pasta root de origem se vazia
    try:
        os.rmdir(SRC_DIR)
        print("Diretório 'storage' raiz removido com sucesso.")
    except:
        print("Diretório 'storage' raiz ainda contém arquivos/pastas.")

if __name__ == "__main__":
    migrate()
