import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Titlul aplicației
st.title('Exemplu simplu Streamlit')

# Text introductiv
st.write('Aceasta este o aplicație simplă de exemplu în Streamlit!')

# Slider pentru a selecta numărul de puncte
num_puncte = st.slider('Selectează numărul de puncte', min_value=10, max_value=100)

# Generarea datelor random
x = np.linspace(0, 10, num_puncte)
y = np.sin(x)

# Crearea unui DataFrame pentru a afișa datele
df = pd.DataFrame({'X': x, 'Y': y})

# Afișarea datelor într-un tabel
st.write('Tabelul de date generate:')
st.write(df)

# Afișarea unui grafic
st.write('Graficul sinusului:')
plt.plot(x, y)
st.pyplot(plt)
