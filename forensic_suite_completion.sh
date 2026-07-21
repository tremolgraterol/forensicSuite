#!/bin/bash
# ForensicSuite - Bash Completion
# Instalar: sudo cp forensic_suite_completion.sh /etc/bash_completion.d/

_forensic_suite_completions()
{
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    commands="hash verificar bloquear desbloquear listar acta firmar verificar-firma claves timestamp manifest verificar-manifest carve analyze memoria perito daemon"
    
    # Primer argumento: mostrar comandos
    if [ ${COMP_CWORD} -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # Si empieza con -, completar opciones segun el comando
    if [[ "${cur}" == -* ]]; then
        local cmd="${COMP_WORDS[1]}"
        case "${cmd}" in
            hash)           COMPREPLY=( $(compgen -W "-a -g --algoritmo --guardar" -- ${cur}) ); return 0 ;;
            verificar)      COMPREPLY=( $(compgen -W "-a --algoritmo" -- ${cur}) ); return 0 ;;
            listar)         COMPREPLY=( $(compgen -W "-s --incluir-sistema" -- ${cur}) ); return 0 ;;
            acta)           COMPREPLY=( $(compgen -W "--perito --cedula --cargo --caso -t --transferir --cerrar --autoridad -o --salida --json" -- ${cur}) ); return 0 ;;
            firmar)         COMPREPLY=( $(compgen -W "--key -o --salida" -- ${cur}) ); return 0 ;;
            timestamp)      COMPREPLY=( $(compgen -W "--tsa -a --algoritmo -o --token-salida" -- ${cur}) ); return 0 ;;
            manifest)       COMPREPLY=( $(compgen -W "--caso --perito -o --salida -e --extensiones -x --excluir -v --verificar" -- ${cur}) ); return 0 ;;
            carve)          COMPREPLY=( $(compgen -W "-o --salida --caso --perito -c --config -p --perfil --perfiles -m --manifest -v --verbose --verificar-instalacion --listar-tipos" -- ${cur}) ); return 0 ;;
            memoria)        COMPREPLY=( $(compgen -W "--verificar-entorno --adquirir --analizar --verificar --dump --plugin --caso --directorio --estado --cadena --cifrar --firmar --informe" -- ${cur}) ); return 0 ;;
            perito)         COMPREPLY=( $(compgen -W "--configurar --ver --info" -- ${cur}) ); return 0 ;;
            daemon)         COMPREPLY=( $(compgen -W "status install uninstall" -- ${cur}) ); return 0 ;;
        esac
        
        # Opciones de perfil
        case "${prev}" in
            -a|--algoritmo) COMPREPLY=( $(compgen -W "sha256 sha512 md5" -- ${cur}) ); return 0 ;;
            -p|--perfil)    COMPREPLY=( $(compgen -W "recuperacion medios documentos redes cripto general" -- ${cur}) ); return 0 ;;
        esac
    fi
    
    # Para comandos que esperan archivos, completar archivos
    local cmd="${COMP_WORDS[1]}"
    case "${cmd}" in
        hash|verificar|acta|firmar|timestamp|carve)
            # Completar archivos (.hash, .raw, .txt, etc)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        bloquear|desbloquear)
            # Completar dispositivos /dev/sd*
            COMPREPLY=( $(compgen -G "/dev/sd*" -- ${cur}) )
            return 0
            ;;
    esac
    
    # Por defecto: completar archivos
    COMPREPLY=( $(compgen -f -- ${cur}) )
    return 0
}

complete -F _forensic_suite_completions forensic_suite
complete -F _forensic_suite_completions fs
