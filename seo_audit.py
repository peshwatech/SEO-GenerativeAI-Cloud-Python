def run_enhanced_seo_audit(domain, max_pages=50):
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse
    from collections import Counter, defaultdict
    import xml.etree.ElementTree as ET
    import pandas as pd
    import re, json
    import time
    from urllib.robotparser import RobotFileParser

    # Enhanced keyword extraction with better filtering
    def get_keywords(text, min_length=4, max_length=20):
        # Remove common stop words and improve keyword extraction
        stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'know', 'want', 
                     'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here',
                     'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than',
                     'them', 'well', 'were', 'what', 'your', 'page', 'website', 'site'}
        
        # Extract words and filter
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',' + str(max_length) + '}\b', text.lower())
        filtered_words = [word for word in words if word not in stop_words and not word.isdigit()]
        return Counter(filtered_words)

    # Enhanced title and meta description analysis
    def analyze_title_meta(title, meta_desc, url):
        issues = []
        recommendations = []
        
        # Title analysis
        if not title or title == "N/A":
            issues.append("Missing title tag")
        else:
            if len(title) < 30:
                issues.append("Title too short")
                recommendations.append("Expand title to 50-60 characters")
            elif len(title) > 60:
                issues.append("Title too long")
                recommendations.append("Shorten title to under 60 characters")
            
            # Check for duplicate words
            title_words = title.lower().split()
            if len(title_words) != len(set(title_words)):
                issues.append("Duplicate words in title")
        
        # Meta description analysis
        if not meta_desc or meta_desc == "N/A":
            issues.append("Missing meta description")
        else:
            if len(meta_desc) < 120:
                issues.append("Meta description too short")
                recommendations.append("Expand meta description to 150-160 characters")
            elif len(meta_desc) > 160:
                issues.append("Meta description too long")
                recommendations.append("Shorten meta description to under 160 characters")
        
        return {
            "title_length": len(title) if title != "N/A" else 0,
            "meta_desc_length": len(meta_desc) if meta_desc != "N/A" else 0,
            "issues": issues,
            "recommendations": recommendations
        }

    # Enhanced header tag analysis
    def analyze_headers(h1_tags, h2_tags, h3_tags):
        issues = []
        recommendations = []
        
        # H1 analysis
        if not h1_tags:
            issues.append("Missing H1 tag")
        elif len(h1_tags) > 1:
            issues.append("Multiple H1 tags")
            recommendations.append("Use only one H1 tag per page")
        
        # Header hierarchy
        total_headers = len(h1_tags) + len(h2_tags) + len(h3_tags)
        if total_headers == 0:
            issues.append("No header tags found")
        elif total_headers < 3:
            recommendations.append("Add more header tags for better content structure")
        
        return {
            "h1_count": len(h1_tags),
            "h2_count": len(h2_tags),
            "h3_count": len(h3_tags),
            "issues": issues,
            "recommendations": recommendations
        }

    # Enhanced URL structure analysis
    def analyze_url_structure(url):
        parsed = urlparse(url)
        path = parsed.path
        issues = []
        recommendations = []
        
        # Depth analysis
        depth = len(path.strip("/").split("/")) if path.strip("/") else 0
        if depth > 4:
            issues.append("URL too deep")
            recommendations.append("Reduce URL depth to 3 levels or less")
        
        # Character analysis
        if "_" in path:
            issues.append("Contains underscores")
            recommendations.append("Replace underscores with hyphens")
        
        if not re.search(r"[a-zA-Z]", path):
            issues.append("No descriptive text in URL")
            recommendations.append("Add descriptive keywords to URL")
        
        # Length analysis
        if len(url) > 100:
            issues.append("URL too long")
            recommendations.append("Shorten URL to under 100 characters")
        
        # Check for parameters
        if parsed.query:
            issues.append("Contains URL parameters")
        
        return {
            "depth": depth,
            "length": len(url),
            "issues": issues,
            "recommendations": recommendations,
            "score": "Good" if not issues else "Needs Improvement"
        }

    # Content quality analysis
    def analyze_content_quality(word_count, keyword_density, text_content):
        issues = []
        recommendations = []
        
        # Word count analysis
        if word_count < 300:
            issues.append("Content too short")
            recommendations.append("Expand content to at least 300 words")
        elif word_count > 3000:
            recommendations.append("Consider breaking long content into multiple pages")
        
        # Keyword density analysis
        if keyword_density:
            top_keyword_density = max(keyword_density.values()) / word_count * 100
            if top_keyword_density > 3:
                issues.append("Keyword over-optimization")
                recommendations.append("Reduce keyword density to 2-3%")
        
        # Readability check (simple)
        sentences = len(re.split(r'[.!?]+', text_content))
        if sentences > 0:
            avg_words_per_sentence = word_count / sentences
            if avg_words_per_sentence > 20:
                recommendations.append("Consider shorter sentences for better readability")
        
        return {
            "word_count": word_count,
            "readability_score": "Good" if word_count >= 300 else "Poor",
            "issues": issues,
            "recommendations": recommendations
        }

    # Extract all page URLs with better error handling
    def extract_all_page_urls(sitemap_url):
        try:
            page_urls = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(sitemap_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Handle different content types
            if 'xml' in response.headers.get('content-type', ''):
                root = ET.fromstring(response.content)
                
                # Check for sitemap index
                sitemap_tags = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap")
                if sitemap_tags:
                    for sitemap in sitemap_tags:
                        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                        if loc is not None:
                            page_urls.extend(extract_all_page_urls(loc.text.strip()))
                else:
                    # Regular sitemap
                    for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                        page_urls.append(url.text.strip())
            
            return page_urls[:max_pages]  # Limit number of pages
        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")
            return []

    # Enhanced breadcrumb extraction
    def extract_breadcrumbs(soup):
        breadcrumbs = []
        
        # Try multiple selectors
        selectors = [
            'nav[aria-label*="breadcrumb" i]',
            '.breadcrumb',
            '.breadcrumbs',
            '[class*="breadcrumb"]',
            '.elementor-widget-breadcrumbs'
        ]
        
        for selector in selectors:
            container = soup.select_one(selector)
            if container:
                links = container.find_all(['a', 'span'])
                breadcrumbs = [link.get_text(strip=True) for link in links if link.get_text(strip=True)]
                if breadcrumbs:
                    break
        
        # JSON-LD fallback
        if not breadcrumbs:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
                        for item in data.get("itemListElement", []):
                            if item.get("name"):
                                breadcrumbs.append(item.get("name"))
                except:
                    continue
        
        return breadcrumbs

    # Enhanced internal linking analysis
    def analyze_internal_links(soup, base_url):
        internal_links = []
        external_links = []
        
        for a in soup.find_all("a", href=True):
            href = a.get('href', '').strip()
            if not href or href.startswith('#'):
                continue
                
            full_url = urljoin(base_url, href)
            parsed_base = urlparse(base_url)
            parsed_link = urlparse(full_url)
            
            if parsed_link.netloc == parsed_base.netloc:
                internal_links.append({
                    'url': full_url,
                    'anchor_text': a.get_text(strip=True),
                    'title': a.get('title', '')
                })
            else:
                external_links.append({
                    'url': full_url,
                    'anchor_text': a.get_text(strip=True)
                })
        
        return internal_links, external_links

    # Calculate SEO score
    def calculate_seo_score(title_meta, header, url, content, internal_links, images_without_alt):
        score = 100
        
        # Deduct points for issues
        score -= len(title_meta["issues"]) * 10
        score -= len(header["issues"]) * 10
        score -= len(url["issues"]) * 5
        score -= len(content["issues"]) * 10
        score -= min(images_without_alt * 2, 20)  # Cap at 20 points
        
        # Bonus for good internal linking
        if internal_links >= 3:
            score += 5
        
        return max(0, min(100, score))

    # Main SEO data extraction function
    def get_seo_data(url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Basic SEO elements
            title = soup.title.string.strip() if soup.title else "N/A"
            
            desc_tag = soup.find("meta", attrs={"name": "description"})
            meta_description = desc_tag.get("content", "").strip() if desc_tag else "N/A"
            
            keywords_tag = soup.find("meta", attrs={"name": "keywords"})
            meta_keywords = keywords_tag.get("content", "").strip() if keywords_tag else "N/A"
            
            robots_tag = soup.find("meta", attrs={"name": "robots"})
            robots_content = robots_tag.get("content", "").strip().lower() if robots_tag else "index,follow"
            
            # Header tags
            h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
            h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
            h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]
            
            # Images and alt texts
            images = soup.find_all("img")
            alt_texts = [img.get("alt", "").strip() for img in images if img.get("alt")]
            images_without_alt = len([img for img in images if not img.get("alt")])
            
            # Content analysis
            page_text = soup.get_text(separator=' ', strip=True)
            word_count = len(page_text.split())
            keyword_density = get_keywords(page_text)
            
            # Links analysis
            internal_links, external_links = analyze_internal_links(soup, url)
            
            # Breadcrumbs
            breadcrumbs = extract_breadcrumbs(soup)
            
            # Analysis
            title_meta_analysis = analyze_title_meta(title, meta_description, url)
            header_analysis = analyze_headers(h1_tags, h2_tags, h3_tags)
            url_analysis = analyze_url_structure(url)
            content_analysis = analyze_content_quality(word_count, keyword_density, page_text)
            
            return {
                "URL": url,
                "Title": title,
                "Title Length": title_meta_analysis["title_length"],
                "Meta Description": meta_description,
                "Meta Description Length": title_meta_analysis["meta_desc_length"],
                "Meta Keywords": meta_keywords,
                "H1 Tags": h1_tags,
                "H2 Tags": h2_tags,
                "H3 Tags": h3_tags,
                "H1 Count": header_analysis["h1_count"],
                "H2 Count": header_analysis["h2_count"],
                "H3 Count": header_analysis["h3_count"],
                "Images Total": len(images),
                "Images Without Alt": images_without_alt,
                "Alt Texts": alt_texts,
                "Breadcrumbs": breadcrumbs,
                "Internal Links": internal_links,
                "External Links": external_links,
                "Internal Links Count": len(internal_links),
                "External Links Count": len(external_links),
                "Word Count": word_count,
                "Keyword Density": keyword_density,
                "Top Keywords": keyword_density.most_common(10),
                "Robots": robots_content,
                "URL Depth": url_analysis["depth"],
                "URL Length": url_analysis["length"],
                "Title Meta Issues": title_meta_analysis["issues"],
                "Header Issues": header_analysis["issues"],
                "URL Issues": url_analysis["issues"],
                "Content Issues": content_analysis["issues"],
                "Recommendations": (title_meta_analysis["recommendations"] + 
                                 header_analysis["recommendations"] + 
                                 url_analysis["recommendations"] + 
                                 content_analysis["recommendations"]),
                "Overall Score": calculate_seo_score(title_meta_analysis, header_analysis, 
                                                   url_analysis, content_analysis, 
                                                   len(internal_links), images_without_alt)
            }
            
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return {"URL": url, "Error": str(e)}

    # Generate comprehensive report
    def generate_comprehensive_report(df):
        report = {
            "summary": {},
            "common_issues": [],
            "keyword_analysis": {},
            "recommendations": []
        }
        
        # Handle empty dataframe
        if df.empty:
            return report
            
        # Filter out error rows - fix the boolean indexing issue
        if 'Error' in df.columns:
            valid_df = df[df['Error'].isna()]
        else:
            valid_df = df
        
        if valid_df.empty:
            return report
        
        # Summary statistics
        report["summary"] = {
            "total_pages": len(valid_df),
            "average_score": valid_df["Overall Score"].mean() if "Overall Score" in valid_df.columns else 0,
            "pages_with_issues": len(valid_df[valid_df["Title Meta Issues"].astype(str) != "[]"]),
            "average_word_count": valid_df["Word Count"].mean() if "Word Count" in valid_df.columns else 0,
            "pages_missing_meta_desc": len(valid_df[valid_df["Meta Description"] == "N/A"]),
            "pages_missing_h1": len(valid_df[valid_df["H1 Count"] == 0])
        }
        
        # Most common issues
        all_issues = []
        for issues_col in ["Title Meta Issues", "Header Issues", "URL Issues", "Content Issues"]:
            if issues_col in valid_df.columns:
                for issues in valid_df[issues_col]:
                    if isinstance(issues, list):
                        all_issues.extend(issues)
        
        issue_counter = Counter(all_issues)
        report["common_issues"] = issue_counter.most_common(10)
        
        # Keyword analysis
        all_keywords = Counter()
        for keywords in valid_df["Top Keywords"]:
            if isinstance(keywords, list):
                for keyword, count in keywords:
                    all_keywords[keyword] += count
        
        report["keyword_analysis"] = {
            "top_keywords": all_keywords.most_common(20),
            "total_unique_keywords": len(all_keywords),
            "keyword_opportunities": [kw for kw, count in all_keywords.items() if count == 1][:10]
        }
        
        return report

    # === Main execution ===
    print(f"🔍 Starting SEO audit for {domain}")
    
    # Normalize domain URL
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    
    # Check robots.txt
    robots_url = domain.rstrip("/") + "/robots.txt"
    try:
        robots_response = requests.get(robots_url, timeout=10)
        if robots_response.status_code == 200:
            print("✅ Robots.txt found")
        else:
            print("⚠️  Robots.txt not found")
    except Exception as e:
        print(f"⚠️  Could not check robots.txt: {e}")
    
    # Get sitemap URLs
    sitemap_url = domain.rstrip("/") + "/sitemap.xml"
    all_page_urls = extract_all_page_urls(sitemap_url)
    
    if not all_page_urls:
        print("⚠️  No sitemap found or sitemap empty, using homepage only...")
        all_page_urls = [domain.rstrip("/")]
    
    print(f"✅ Found {len(all_page_urls)} URLs to audit")
    
    # Audit pages
    seo_reports = []
    for i, url in enumerate(all_page_urls[:max_pages]):
        print(f"Auditing ({i+1}/{min(len(all_page_urls), max_pages)}): {url}")
        result = get_seo_data(url)
        seo_reports.append(result)
        time.sleep(1)  # Be respectful to the server
    
    # Create DataFrame
    df = pd.DataFrame(seo_reports)
    
    # Generate comprehensive report
    comprehensive_report = generate_comprehensive_report(df)
    
    # Print summary
    print("\n" + "="*50)
    print("📊 SEO AUDIT SUMMARY")
    print("="*50)
    
    if comprehensive_report['summary']:
        print(f"Total Pages Analyzed: {comprehensive_report['summary']['total_pages']}")
        print(f"Average SEO Score: {comprehensive_report['summary']['average_score']:.1f}/100")
        print(f"Pages with Issues: {comprehensive_report['summary']['pages_with_issues']}")
        print(f"Average Word Count: {comprehensive_report['summary']['average_word_count']:.0f}")
        
        if comprehensive_report['common_issues']:
            print("\n🔥 Top Issues Found:")
            for issue, count in comprehensive_report['common_issues'][:5]:
                print(f"  • {issue}: {count} pages")
        
        if comprehensive_report['keyword_analysis']['top_keywords']:
            print("\n🔑 Top Keywords:")
            for keyword, count in comprehensive_report['keyword_analysis']['top_keywords'][:10]:
                print(f"  • {keyword}: {count} occurrences")
        
        if comprehensive_report['keyword_analysis']['keyword_opportunities']:
            print("\n💡 Keyword Opportunities:")
            for keyword in comprehensive_report['keyword_analysis']['keyword_opportunities'][:5]:
                print(f"  • {keyword}")
    else:
        print("No valid pages found to analyze")
    
    return df, comprehensive_report

# Fixed helper function to create detailed page report
def create_detailed_page_report(df, url):
    """Create a detailed report for a specific page"""
    # Filter the dataframe for the specific URL
    page_df = df[df['URL'] == url]
    
    if page_df.empty:
        print(f"\n❌ No data found for URL: {url}")
        print("Available URLs in the dataset:")
        for available_url in df['URL'].head(10):
            print(f"  • {available_url}")
        return
    
    # Check if there's an error for this page
    if 'Error' in page_df.columns and page_df['Error'].notna().any():
        print(f"\n❌ Error occurred while processing {url}")
        print(f"Error: {page_df['Error'].iloc[0]}")
        return
    
    page_data = page_df.iloc[0]
    
    print(f"\n📄 DETAILED PAGE REPORT: {url}")
    print("="*60)
    
    # Check if required columns exist
    if 'Overall Score' in page_data:
        print(f"SEO Score: {page_data['Overall Score']}/100")
    
    if 'Title' in page_data and 'Title Length' in page_data:
        print(f"Title: {page_data['Title']} ({page_data['Title Length']} chars)")
    
    if 'Meta Description' in page_data and 'Meta Description Length' in page_data:
        print(f"Meta Description: {page_data['Meta Description']} ({page_data['Meta Description Length']} chars)")
    
    if 'Word Count' in page_data:
        print(f"Word Count: {page_data['Word Count']}")
    
    if 'Internal Links Count' in page_data:
        print(f"Internal Links: {page_data['Internal Links Count']}")
    
    if 'H1 Count' in page_data:
        print(f"H1 Count: {page_data['H1 Count']}")
    
    if 'H2 Count' in page_data:
        print(f"H2 Count: {page_data['H2 Count']}")
    
    if 'Images Without Alt' in page_data:
        print(f"Images without Alt: {page_data['Images Without Alt']}")
    
    # Display issues
    issues_columns = ['Title Meta Issues', 'Header Issues', 'URL Issues', 'Content Issues']
    all_issues = []
    for col in issues_columns:
        if col in page_data and isinstance(page_data[col], list):
            all_issues.extend(page_data[col])
    
    if all_issues:
        print(f"\n❌ Issues Found: {', '.join(all_issues)}")
    
    # Display recommendations
    if 'Recommendations' in page_data and isinstance(page_data['Recommendations'], list) and page_data['Recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in page_data['Recommendations']:
            print(f"  • {rec}")

# Example usage with error handling
def safe_run_audit(domain, max_pages=10):
    """Safe wrapper for running the audit with error handling"""
    try:
        df, report = run_enhanced_seo_audit(domain, max_pages=max_pages)
        
        # Save results if successful
        if not df.empty:
            df.to_csv("enhanced_seo_audit.csv", index=False)
            print(f"\n✅ Results saved to enhanced_seo_audit.csv")
            
            # Create detailed report for the first valid URL
            if 'Error' in df.columns:
                valid_urls = df[df['Error'].isna()]['URL']
            else:
                valid_urls = df['URL']
                
            if not valid_urls.empty:
                create_detailed_page_report(df, valid_urls.iloc[0])
        
        return df, report
        
    except Exception as e:
        print(f"❌ Error running audit: {e}")
        return pd.DataFrame(), {}

# Run the audit
if __name__ == "__main__":
    domain = "https://taleeftech.com"
    df, report = safe_run_audit(domain, max_pages=10)
