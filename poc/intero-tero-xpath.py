#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coletor de URL "Inteiro Teor" - STF - PLAYWRIGHT HEADLESS
Autor: Chico Alff
Versão: 2.2
Data: 14/10/2025
"""

import asyncio
import requests
from playwright.async_api import async_playwright


async def coletar_inteiro_teor_playwright_headless():
    """
    Versão headless para ambientes sem interface gráfica
    """
    playwright = None
    browser = None
    
    try:
        print("🚀 INICIANDO COLETOR STF - PLAYWRIGHT HEADLESS")
        print("=" * 50)
        
        # URL REAL FORNECIDA
        URL_REAL = "https://jurisprudencia.stf.jus.br/pages/search/sjur229171/false"
        XPATH_EXATO = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]/div/div/div[1]/div[2]/div/mat-icon[2]"
        
        print(f"🎯 Configurando automação HEADLESS...")
        print(f"   URL: {URL_REAL}")
        print(f"   XPath: {XPATH_EXATO}")
        print("=" * 50)
        
        # Iniciar Playwright em modo HEADLESS
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,  # 🔥 MUDANÇA CRÍTICA: Agora é True
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
        
        # Estratégias de busca em ordem de prioridade
        selectors = [
            f"xpath={XPATH_EXATO}",
            "[mattooltip='Inteiro teor']",
            "mat-icon[mattooltip='Inteiro teor']",
            "//*[@mattooltip='Inteiro teor']"
        ]
        
        elemento = None
        for selector in selectors:
            try:
                if selector.startswith("xpath="):
                    elemento = await page.wait_for_selector(selector, timeout=10000)
                else:
                    elemento = await page.query_selector(selector)
                
                if elemento:
                    print(f"✅ Elemento encontrado com: {selector}")
                    break
            except:
                continue
        
        if not elemento:
            raise Exception("Elemento 'Inteiro teor' não encontrado com nenhum seletor")
        
        # Verificar elemento
        tooltip = await elemento.get_attribute("mattooltip")
        print(f"   Tooltip: '{tooltip}'")
        
        print("🖱️ Clicando no botão 'Inteiro Teor'...")
        
        # Estratégia: aguardar popup e clicar
        async with page.expect_popup() as popup_info:
            await elemento.click()
        
        print("⏳ Aguardando nova aba/popup...")
        new_page = await popup_info.value
        await new_page.wait_for_load_state('networkidle')
        await new_page.wait_for_timeout(2000)
        
        # Capturar URL da nova aba
        url_jsp = new_page.url
        print(f"🌐 URL JSP capturada: {url_jsp}")
        
        # Fechar nova aba
        await new_page.close()
        
        if not url_jsp:
            print("❌ Não foi possível capturar URL JSP")
            return None
        
        # Resolver redirecionamento para URL final
        print("🔄 Resolvendo redirecionamento final...")
        pdf_url = await resolver_redirecionamento_async(url_jsp)
        
        if pdf_url:
            print("\n" + "="*60)
            print("🎉 SUCESSO! URL DO PDF ENCONTRADA:")
            print("="*60)
            print(f"📄 {pdf_url}")
            print("="*60)
            
            # Salvar em arquivo
            with open("url_pdf_coletada.txt", "w") as f:
                f.write(pdf_url)
            print("💾 URL salva em: url_pdf_coletada.txt")
            
            return pdf_url
        else:
            print("❌ Não foi possível obter URL final do PDF")
            return None
            
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


async def resolver_redirecionamento_async(jsp_url):
    """
    Resolve redirecionamento JSP de forma assíncrona
    """
    try:
        print(f"   URL JSP: {jsp_url}")
        
        # Usar requests (síncrono) para redirecionamento
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        response = session.get(jsp_url, allow_redirects=True, timeout=30)
        final_url = response.url
        
        print(f"   URL final: {final_url}")
        
        # Verificar se é PDF
        if '.pdf' in final_url.lower():
            print("✅ Confirmação: URL aponta para PDF")
        else:
            print("⚠️  Aviso: URL não parece ser PDF direto")
            
        return final_url
        
    except Exception as e:
        print(f"❌ Erro no redirecionamento: {e}")
        return None


async def main():
    """Execução principal"""
    resultado = await coletar_inteiro_teor_playwright_headless()
    
    if resultado:
        print("\n✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"📎 PDF disponível em: {resultado}")
    else:
        print("\n❌ FALHA NO PROCESSO")


# Versão ultra-simplificada para teste
async def teste_ultra_simples():
    """Teste mínimo com Playwright"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Headless=True
        page = await browser.new_page()
        
        try:
            url = "https://jurisprudencia.stf.jus.br/pages/search/sjur229171/false"
            print(f"🌐 Acessando: {url}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # XPATH EXATO
            xpath = "/html/body/app-root/app-home/main/app-search-detail/div/div/div[1]/mat-tab-group/div/mat-tab-body[1]/div/div/div[1]/div[2]/div/mat-icon[2]"
            
            print("🎯 Clicando no elemento...")
            
            async with page.expect_popup() as popup_info:
                await page.click(f"xpath={xpath}")
            
            new_page = await popup_info.value
            await new_page.wait_for_load_state('networkidle')
            
            url_capturada = new_page.url
            print(f"🔗 URL capturada: {url_capturada}")
            
            await new_page.close()
            
            # Resolver redirecionamento
            session = requests.Session()
            response = session.get(url_capturada, allow_redirects=True)
            pdf_final = response.url
            
            print(f"📄 PDF final: {pdf_final}")
            return pdf_final
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("🚀 Executando Coletor STF em modo HEADLESS...")
    asyncio.run(main())
    
    # Para teste rápido, descomente:
    # resultado = asyncio.run(teste_ultra_simples())
    # print(f"Resultado: {resultado}")