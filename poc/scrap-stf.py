#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de URL JSP "Inteiro Teor" - STF - PLAYWRIGHT HEADLESS
Autor: Chico Alff
Versão: 2.3
Data: 14/10/2025
"""

import asyncio
from playwright.async_api import async_playwright


async def obter_url_jsp_stf():
    """
    Versão simplificada - apenas obtém a URL JSP do Inteiro Teor
    """
    playwright = None
    browser = None
    
    try:
        print("🚀 INICIANDO COLETOR URL JSP - STF")
        print("=" * 50)
        
        # URL REAL FORNECIDA
        URL_REAL = "https://jurisprudencia.stf.jus.br/pages/search/sjur229171/false"
        XPATH_EXATO = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]/div/div/div[1]/div[2]/div/mat-icon[2]"
        
        print(f"🎯 Configurando automação...")
        print(f"   URL: {URL_REAL}")
        print(f"   XPath: {XPATH_EXATO}")
        print("=" * 50)
        
        # Iniciar Playwright em modo HEADLESS
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        # Configurar contexto
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = await context.new_page()
        
        print("🌐 Navegando para a página do STF...")
        await page.goto(URL_REAL, wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        print("🔍 Localizando botão 'Inteiro Teor'...")
        
        # Buscar elemento com XPath exato
        elemento = await page.wait_for_selector(f"xpath={XPATH_EXATO}", timeout=15000)
        
        # Verificar elemento
        tooltip = await elemento.get_attribute("mattooltip")
        classe = await elemento.get_attribute("class")
        
        print(f"✅ Elemento encontrado!")
        print(f"   📝 Tooltip: '{tooltip}'")
        print(f"   📝 Classe: '{classe}'")
        
        print("🖱️ Clicando no botão 'Inteiro Teor'...")
        
        # Estratégia: aguardar popup e clicar
        async with page.expect_popup() as popup_info:
            await elemento.click()
        
        print("⏳ Aguardando nova aba/popup...")
        new_page = await popup_info.value
        await new_page.wait_for_load_state('networkidle')
        await new_page.wait_for_timeout(2000)
        
        # Capturar URL da nova aba (URL JSP)
        url_jsp = new_page.url
        print(f"🌐 URL JSP capturada: {url_jsp}")
        
        # Fechar nova aba
        await new_page.close()
        
        print("\n" + "="*60)
        print("🎉 URL JSP OBTIDA COM SUCESSO!")
        print("="*60)
        print(f"🔗 {url_jsp}")
        print("="*60)
        
        return url_jsp
            
    except Exception as e:
        print(f"💥 Erro durante a automação: {e}")
        return None
        
    finally:
        # Limpeza
        if browser:
            print("🔒 Fechando navegador...")
            await browser.close()
        if playwright:
            await playwright.stop()


async def main():
    """Execução principal"""
    url_jsp = await obter_url_jsp_stf()
    
    if url_jsp:
        print("\n✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"📎 URL JSP disponível: {url_jsp}")
        
        # Salvar URL JSP em arquivo
        with open("url_jsp_coletada.txt", "w") as f:
            f.write(url_jsp)
        print("💾 URL JSP salva em: url_jsp_coletada.txt")
    else:
        print("\n❌ FALHA: Não foi possível obter a URL JSP")


# Versão ultra-rápida para teste
async def teste_rapido_jsp():
    """Teste mínimo - apenas URL JSP"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = "https://jurisprudencia.stf.jus.br/pages/search/sjur229171/false"
            xpath = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]/div/div/div[1]/div[2]/div/mat-icon[2]"
            
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            async with page.expect_popup() as popup_info:
                await page.click(f"xpath={xpath}")
            
            new_page = await popup_info.value
            await new_page.wait_for_load_state('networkidle')
            
            url_jsp = new_page.url
            await new_page.close()
            
            return url_jsp
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("🚀 Executando Coletor URL JSP...")
    asyncio.run(main())