"use client"
import { useEffect, useState } from 'react';
import axios from 'axios';
import * as cheerio from 'cheerio';

interface Article {
  title: string;
  link: string;
  summary: string;
}

const Home = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const response = await axios.get('https://thehackernews.com/search/label/Cyber%20Attack');
        const html = response.data;
        const $ = cheerio.load(html);

        const articlesData: Article[] = [];

        $('div.post').each((index, element) => {
          const title = $(element).find('h2 a').text();
          const link = $(element).find('h2 a').attr('href')!;
          const summary = $(element).find('.entry-summary').text().trim();

          articlesData.push({
            title,
            link,
            summary
          });
        });

        setArticles(articlesData);
      } catch (err) {
        setError('Failed to load articles');
      } finally {
        setLoading(false);
      }
    };

    fetchArticles();
  }, []);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <p className="text-red-500">{error}</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 p-4 text-center">
        <h1 className="text-3xl font-bold">Cyber Attack News</h1>
      </header>

      <main className="p-6">
        <div className="max-w-4xl mx-auto">
          {articles.length > 0 ? (
            articles.map((article, index) => (
              <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-lg mb-6">
                <h2 className="text-xl font-semibold text-blue-400">
                  <a href={article.link} target="_blank" rel="noopener noreferrer">{article.title}</a>
                </h2>
                <p className="mt-2 text-gray-300">{article.summary}</p>
              </div>
            ))
          ) : (
            <p>No articles found.</p>
          )}
        </div>
      </main>

      <footer className="bg-gray-800 text-center p-4 text-gray-400">
        <p>Powered by The Hacker News</p>
      </footer>
    </div>
  );
};

export default Home;
