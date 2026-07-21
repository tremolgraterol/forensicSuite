# 05 - Marco Legal (Venezuela)

## Normativa aplicable

### Ley Especial contra Delitos Informaticos (LECD)

Gaceta Oficial Extraordinaria Nro. 37.313 del 30 de octubre de 2001.

- Define los delitos informaticos y establece penas
- Art. 3: Acceso ilicito a sistemas informaticos
- Art. 5: Intercepcion de datos
- Art. 7: Sabotaje informatico
- Art. 9: Alteracion de datos

### Codigo Organico Procesal Penal (COPP)

- **Art. 183**: Medidas de prueba. El juez podra ordenar cualquier medio de prueba.
- **Art. 187**: Cadena de custodia. Todo objeto, instrumento o evidencia debe mantenerse bajo custody continua documentada.
- **Art. 191**: Prueba ilicita. Es nula la prueba obtenida con violacion a garantias constitucionales.
- **Art. 224**: Peritos. Son designados por el juez y deben estar juramentados.
- **Art. 225**: Dictamen pericial. Debe contener descripcion detallada del metodo utilizado.

### Ley sobre Mensajes de Datos y Firmas Electronicas

Gaceta Oficial Nro. 39.575 del 7 de febrero de 2012.

- **Art. 2**: Define mensajes de datos como informacion generada por medios electronicos.
- **Art. 6**: La firma electronica satisface el requisito de firma autografa.
- Reconoce valor probatorio a los mensajes de datos.

### Manual Unico de Cadena de Custodia (MP 2017)

Formato oficial del Ministerio Publico de Venezuela con 6 secciones:

1. Identificacion de la evidencia
2. Colector
3. Transporte
4. Receptor / Analista
5. Transferencias sucesivas
6. Devolucion o destruccion

## Implicaciones legales de ForensicSuite

### Bloqueo de escritura

- **Base legal**: ISO 27037 seccion 5.4, COPP Art. 187
- **Obligatorio**: La evidencia debe preservarse en estado original
- **Consecuencia**: Si no se bloqueo, la evidencia puede ser declarada ilicita (COPP Art. 191)

### Hashes criptograficos

- **Base legal**: ISO 27037, NIST SP 800-86, COPP Art. 225
- **Funcion**: Prueba de integridad de la evidencia
- **Consecuencia**: Sin hashes no hay forma de demostrar que la evidencia no fue alterada

### Cadena de custodia

- **Base legal**: COPP Art. 187, Manual MP 2017
- **Obligatorio**: Documentar cada transferencia de evidencia
- **Consecuencia**: Sin cadena de custodia valida, la evidencia puede ser excluida

### Firma digital (GPG)

- **Base legal**: Ley de Mensajes de Datos Art. 6
- **Limitacion**: GPG no es PSC acreditado por SUSCERTE
- **Recomendacion**: Para uso judicial, considerar PSC acreditado

### Sello de tiempo (RFC 3161)

- **Base legal**: Ley de Mensajes de Datos, ISO 27037
- **Funcion**: Prueba de existencia en momento especifico
- **Recomendacion**: Usar TSA publicos reconocidos (DigiCert, Sectigo)

## Advertencia para el perito

1. ForensicSuite es una herramienta de APOYO. No reemplaza el criterio del perito.
2. Los resultados deben ser interpretados por un experto cualificado.
3. Para uso judicial, se recomienda usar PSC acreditados para firma y sello de tiempo.
4. El perito debe documentar en su informe:
   - Version de ForensicSuite utilizada
   - Sistema operativo y configuracion del equipo
   - Comandos exactos ejecutados
   - Resultados obtenidos
5. El contra perito tiene derecho a verificar todos los resultados usando las guias en `docs/`.

## Jurisprudencia relevante

La jurisprudencia venezolana ha establecido que:

- La cadena de custodia es requisito de validez de la prueba digital
- Los hashes criptograficos son medios validos para probar integridad
- La ausencia de bloqueo de escritura puede invalidar la evidencia
- Las firmas electronicas tienen valor probatorio

## Normas internacionales de referencia

| Norma | Titulo | Aplicacion |
|---|---|---|
| ISO 27037 | Identification, collection, acquisition, preservation | Metodologia general |
| NIST SP 800-86 | Guide to Integrating Forensic Techniques | Integracion de herramientas |
| RFC 3161 | Internet X.509 PKI Time-Stamp Protocol | Sello de tiempo |
| RFC 3227 | Guidelines for Evidence Collection | Recoleccion de evidencia |
| FIPS 180-4 | Secure Hash Standard | Algoritmos SHA |
