import re
import math
import difflib

import httpx
from bs4 import BeautifulSoup

class ScrapeWebText:
    def __init__(self,):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537'}
    
    async def fetch_website_text(self, url: str) -> str:
        html_response  = await self.search_api(request_url=url, headers=self.headers)
        html_text = html_response.text
        # html_text = requests.get(url, headers=self.headers).text
        soup = BeautifulSoup(html_text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = ""
        for p in paragraphs:
            if len(p.text) >= 100:
                if p.text.endswith('.') or p.text.endswith('!') or p.text.endswith('?'):
                    text += p.text[:-1] + f"{p.text[-1]} "
                else:
                    text += p.text + "."
        return text

    async def search_api(self, request_url, headers):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                search_response = await client.request(
                    method='get',
                    url=request_url,
                    headers=headers
                )
                await client.aclose()
                return search_response
        except Exception as e:
            print(f"Custom Exception func(search_api): {e}")
            return []
    
    def preprocess_text(self, text: str) -> str:
        text = re.sub(r'\n\s{2,}\n', '\n',text)
        text = re.sub(r'\n\t{2,}\n', '\n',text)
        text = re.sub(r'\n{2,}', '\n',text)
        text = re.sub(r'\t{2,}', '\t',text)
        text = re.sub(r'(\n\s*){2,}', '\n\n', text)
        text = re.sub(r'__{2,}', '_',text)
        pattern = r'[^\x00-\x7F]'
        text = re.sub(pattern, ' ', text)
        text = re.sub(r' {2,}', ' ',text)
        text = self.clean_text(text)
        text = text.strip()
        return text

    def clean_text(self, text: str) -> str:
        replacements = {
            "â\x80\x99": "'",
            "â\x80\x9c": '"',
            "â\x80\x9d": '"',
            "â\x80\x93": '-',
            "â\x80\x94": '--',
            "â\x80\x98": "'",
            "â\x80\x9a": ",",
            "â\x80\x9e": '"',
            "â\x80\xa0": ' ',
            "â\x80\xa6": '...',
            "Â\xa0": ' ',
            "â\x80\x99s": "'s",
            "â\x80\x90": '-',    # Hyphen
            "â\x80\x91": '-',    # Non-breaking hyphen
            "â\x80\x92": '-',    # Figure dash
            "â\x80\xa2": '•'     # Bullet
        }
        for key, value in replacements.items():
            text = text.replace(key, value)
        # text = re.sub(r'[^a-zA-Z0-9.,:!?\'"()\[\]{}<> ]', ' ', text) # Remove unwanted characters (preserve only alphanumeric, punctuation, and spaces)
        text = text.strip()
        return text

    async def execute_scrape(self, url: str) -> str:
        raw_text = await self.fetch_website_text(url)
        clean_text = self.preprocess_text(raw_text)
        return clean_text
    
class CreateChunks:
    def __init__(self,):
        pass

    def similar_context_from_snippet(self, text, snippet, context_sentences=2, similarity_threshold=0.3):
        char_thrshold = 1500
        sentences = re.split(r'(?<=[.!?]) +', text)
        snippet_sentence = None
        max_similarity_ratio = 0
        for sentence in sentences:
            similarity_ratio = difflib.SequenceMatcher(None, snippet, sentence).ratio()
            if similarity_ratio > similarity_threshold and similarity_ratio > max_similarity_ratio:
                snippet_sentence = sentence
                max_similarity_ratio = similarity_ratio
        if snippet_sentence is None:
            return snippet
        snippet_index = sentences.index(snippet_sentence)
        context_start = max(0, snippet_index - context_sentences)
        context_end = min(len(sentences), snippet_index + context_sentences + 1)
        
        chunk_text = ' '.join(sentences[context_start:context_end])
        if len(chunk_text) > char_thrshold:
            closest_ = self.rfind_regex(chunk_text)
            if closest_ == -1:
                closest_ = chunk_text.rfind('.') if chunk_text.rfind('.') != -1 else chunk_text.rfind(' ')
                closest_ += 1
            chunk_text = chunk_text[:closest_].strip()

        return chunk_text

    def get_number_of_chunks(self, text, character_threshold):
        if len(text) <= character_threshold:
            return 1
        else:
            chunk_number = 1
            while True:
                div = math.ceil(len(text)/chunk_number)
                if div <  character_threshold:
                    break 
                else:
                    chunk_number += 1
            return chunk_number
        
    def rfind_regex(self, text):
        pattern = r'(?<=[.!?]) +'
        matches = list(re.finditer(pattern, text))
        if matches:
            return matches[-1].end() - 1
        return -1
    
    def split_text_into_parts(self, text, num_parts, max_chunk_length):
        chunk_length = math.ceil(len(text)/num_parts)
        chunks = []
        start_index = 0

        remaining_text = text
        for _ in range(num_parts - 1):
            current_text = remaining_text[:max_chunk_length]
            remaining_text = remaining_text[max_chunk_length:]

            if len(remaining_text) == 0: # For the last
                chunks.append(current_text.strip())
                break

            closest_ = self.rfind_regex(current_text)
            if closest_ == -1:
                closest_ = current_text.rfind('.') if current_text.rfind('.') != -1 else current_text.rfind(' ')
                closest_ += 1

            chunks.append(current_text[:closest_].strip())
            remaining_text = current_text[closest_:] + remaining_text

        return chunks


    def chunk_web_text(self, text):
        character_threshold = 1500
        chunk_number = self.get_number_of_chunks(text, character_threshold)
        if chunk_number == 1:
            return [text]
        chunks = self.split_text_into_parts(text, chunk_number, character_threshold)
        return chunks



if __name__ == "__main__":
    ### Web Search + Scrape
    # url = "https://www.webmd.com/diabetes/understanding-diabetes-symptoms"
    # scraper = ScrapeWebText()
    # text = scraper.execute_scrape(url)
    # print(text)

    ### Create Chunks
    # scraped_text = """Diabetes happens when your blood sugar (blood glucose), which is your body's primary energy source, is too high. There are two types of diabetes:Extreme thirst is one of the most common early symptoms of both type 1 and type 2 diabetes. (Photo credit: iStockGetty Images)Both types of diabetes have some of the same telltale warning signs.Increased hungerYour body converts the food you eat into glucose, which your cells use for energy. But your cells need insulin to take in glucose. If your body doesn't make enough or any insulin, or if your cells resist the insulin your body makes, the glucose can't get into them and you have no energy. This can make you hungrier than usual.Fatigue and tirednessA lack of insulin and glucose can also make you more tired than usual.Peeing more oftenThe average person usually has to pee about four to seven times in 24 hours, but people with diabetes may go a lot more. Why? Normally, your body reabsorbs glucose as it passes through your kidneys. But when diabetes pushes your blood sugar up, your kidneys may not be able to bring it all back in. This causes the body to make more urine, and that takes fluids. The result: You'll have to go more often. You might pee out more, too.Frequent thirstBecause you're peeing so much, you can get very thirsty.Dry mouthBecause your body is using fluids to make pee, there's less moisture for other things. You could get dehydrated, and your mouth may feel dry.Itchy and dry skinYour skin could also feel dry, which may start to itch as well.Blurred visionChanging fluid levels in your body could cause the lenses in your eyes to swell. They would then change shape and be unable to focus.Unintentional weight lossIf your body can't get energy from your food, it will start burning muscle and fat for energy instead. You may lose weight even though you haven't changed how you eat.Can diabetes cause headaches?Headache may be a symptom of hypoglycemia, or low blood sugar. It happens when your sugar or glucose level drops very low.How can you tell if you have diabetes? Most early symptoms are due to higherthannormal glucose levels in your blood. While symptoms of type 1 and type 2 diabetes are the same, there's a difference in how they appear.In type 1 diabetes, symptoms show up quickly, in just a few days or weeks, especially in children. The four most common symptoms are:Type 2 diabetes symptoms may be mild and develop more slowly, especially early on in the disease. It's possible to go for years without realizing you have the condition.There's no major difference in early diabetes signs between men and women, but there may be a few contrasts. Women with the condition may have vaginal yeast infections and urinary tract infections more often, while men with untreated diabetes tend to lose muscle mass.Early symptoms of type 1 diabetes in childrenType 1 diabetes can happen at any age but tends to crop up in children aged 5 to 6 and 11 to 13. Researchers think this is due to hormones at these ages. Symptoms include:Early symptoms of type 2 diabetes in childrenAdults are more likely to get type 2 diabetes, but the disease is happening more often in kids because of obesity. Your child may not show any symptoms of the disease, but here are some to look out for:High blood sugar during pregnancy usually has no symptoms. You might feel a little thirstier than normal, have to pee more often, have a dry mouth, or feel tired.If you have an average chance of getting gestational diabetes, your doctor will likely screen you for the condition between 24 and 28 weeks of pregnancy. But your doctor may test you early in your pregnancy, possibly at your first prenatal visit, if:The screening involves drinking a sugary solution and having your blood sugar tested an hour later. If your blood sugar is high, you'll need a followup test, where you'll drink a stronger solution and have your blood sugar tested every hour for 3 hours.Signs of type 2 diabetes complications may include:Learn about what you can do to lower your risk of diabetes complications.If you're older than 45 or have other risks for diabetes, it's important to get tested. When you spot the condition early, you can avoid nerve damage, heart trouble, and other complications.As a general rule, call your doctor if you:Diabetes often starts with mild symptoms such as feeling very hungry and tired, needing to pee a lot, being very thirsty, having a dry mouth, itchy skin, and blurry vision. Type 1 diabetes symptoms appear quickly and are more severe, while type 2 symptoms develop slowly. It's important to see a doctor if you have symptoms or have a higher chance of getting diabetes to avoid serious health problems.SOURCES:Cleveland Clinic: "Diabetes: Frequently Asked Questions," "What Is Diabetes?" "Diabetes: Preventing Complications," "Hyperglycemia (High Blood Sugar)."University of Michigan Health System: "Type 1 Diabetes."National Diabetes Information Clearinghouse: "Am I at Risk for Type 2 Diabetes? Taking Steps to Lower Your Risk of Getting Diabetes."Baylor Scott White Healthcare: "Urinary Frequency," "Diabetes and Diabetic Neuropathy HardtoHeal Wounds."Sutter Health: "Question Answer: Is Sudden Weight Loss a Sign of Diabetes? If So, Why?"University of Rochester Medical Center: "Diabetic Skin Troubles."Joslin Diabetes Center: "Diseases of the Eye," "Diabetic Neuropathy: What You Need to Know."The Nemours Foundation: "When Blood Sugar Is Too High."Virginia Mason Medical Center: "Complications."Carolinas Health System: "Diabetes: Yeast Infections and Diabetes: What You Should Know."National Institute of Diabetes and Digestive and Kidney Diseases: "Symptoms Causes of Gestational Diabetes," "What is Diabetes?"Geisinger Health: "3 reasons diabetic wounds are slow to heal."American Diabetes Association: "Hyperosmolar Hyperglycemic Nonketotic Syndrome (HHNS)," "Hypoglycemia (Low Blood Glucose)," "Skin Complications."Diabetes Educational Services: "Diabetes Detectives Finding Uncommon Conditions."Merck Manual: "Hypoglycemia."Diabetes UK: "Differences Between Type 1 and Type 2 Diabetes," "Type 1 Diabetes Symptoms."OSF Healthcare: "Don't ignore the early signs of diabetes."Children's Healthcare of Atlanta: "Spotting the Signs of Type 1 Diabetes."Mayo Clinic: "Type 2 diabetes in children," "Gestational Diabetes."NHS: "Gestational Diabetes." 2005 2024 WebMD LLC, an Internet Brands company. All rights reserved. WebMD does not provide medical advice, diagnosis or treatment. See additional information."""
    # chunks = CreateChunks().chunk_web_text(scraped_text)
    # breakpoint()

    def get_context(text, substring, context_sentences=2, similarity_threshold=0.3):
        sentences = re.split(r'(?<=[.!?]) +', text)
        substring_sentence = None
        max_similarity_ratio = 0
        for sentence in sentences:
            similarity_ratio = difflib.SequenceMatcher(None, substring, sentence).ratio()
            if similarity_ratio > similarity_threshold and similarity_ratio > max_similarity_ratio:
                substring_sentence = sentence
                max_similarity_ratio = similarity_ratio
        if substring_sentence is None:
            return substring
        substring_index = sentences.index(substring_sentence)
        context_start = max(0, substring_index - context_sentences)
        context_end = min(len(sentences), substring_index + context_sentences + 1)
        return ' '.join(sentences[context_start:context_end])

    text = "An official website of the United States governmentThe .gov means its official. Federal government websites often end in .gov or .mil. Before sharing sensitive information, make sure youre on a federal government site. The site is secure. The https: ensures that you are connecting to the official website and that any information you provide is encrypted and transmitted securely. The incidence of diabetes mellitus is rapidly increasing, and this condition often results in significant metabolic disease and severe complications. Nurses have a crucial role in monitoring, educating and supporting people with diabetes, as well as their families and significant others. This article provides an overview of the main types and common symptoms of diabetes, its acute and longterm complications and its management. It also outlines the nurse's role in diabetes care, which frequently includes assessing and empowering patients. Keywords: blood glucose clinical diabetes diabetic foot ulcers diabetic ketoacidosis glycaemic control hyperglycaemia hypoglycaemia insulin type 1 diabetes type 2 diabetes. 2021 RCN Publishing Company Ltd. All rights reserved. Not to be copied, transmitted or recorded in any way, in whole or part, without prior permission of the publishers. PubMed DisclaimerNone declaredNCBI Literature ResourcesMeSHPMCBookshelfDisclaimerThe PubMed wordmark and PubMed logo are registered trademarks of the U.S. Department of Health and Human Services (HHS). Unauthorized use of these marks is strictly prohibited.Connect with NLMNational Library of Medicine8600 Rockville Pike Bethesda, MD 20894Web PoliciesFOIAHHS Vulnerability DisclosureHelpAccessibilityCareers"
    substring = "This article provides an overview of the main types and common symptoms of diabetes, its acute and long-term complications and its management. It also outlines the nurse's role in diabetes care, which frequently includes assessing and empowering patients."
    resp = get_context(text, substring, context_sentences=2, similarity_threshold=0.3)
    breakpoint()

    pass