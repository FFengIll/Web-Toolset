import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.swing.text.html.parser.Entity;

import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.DefaultHttpClient;


public class CrawlerTheOne {
	HttpClient hc;
	HttpGet httpget;
	HttpResponse response;
	HttpEntity entity;

	boolean debug=true;
	
	final static int VOL_COUNT=5;
	final static String volUrlStr="http://wufazhuce.com/one/vol.";

	//目标（每一一个语句）前一条item
	Pattern prePattern=Pattern.compile(
			"<div class=\"one-cita\">");
	//html元素
	Pattern htmlPattern=Pattern.compile(
			"<[^<|^>]*>");
	//vol号
	Pattern tituloPat=Pattern.compile("");
	//日期
	Pattern domPat=Pattern.compile("<p class=\"dom\">");
	//年月
	Pattern mayPat=Pattern.compile("<p class=\"may\">");
	
	
	
	/*
	 * 
	 * <div class="fp-one-titulo-pubdate">
                                <p class="titulo">VOL.668</p>
                                <p class="dom">6</p>
                                <p class="may">Aug 2014</p>
                            </div>
	 */
	/*
	愿你比别人更不怕一个人独处，愿日后谈起时你会被自己感动。from 刘同《你的孤独，虽败犹荣》                    </div>
    <div class="one-pubdate">
        <p class="dom">6</p>
        <p class="may">Aug 2014</p>
    </div>
	 */

	private void visitVol(int vol) {
		
		HttpClient hClient=new DefaultHttpClient();
		
		try {
			httpget=new HttpGet(volUrlStr+vol);
			response=hc.execute(httpget);
			entity=response.getEntity();

			getCita(entity);

			httpget.abort();
		} catch (Exception e) {
			// TODO: handle exception
		}finally{
			hClient.getConnectionManager().shutdown();
		}

	}


	private void visitVolsFromTo(int oldvol, int newvol) {
		for (int i = newvol; i >= oldvol; i--) {
			visitVol(i);
		}
	}


	/**
	 * 获取最新的vol编号
	 * @return
	 */
	private int getNewestVol(HttpEntity entity) {

		try {
			InputStream inSm = entity.getContent();
			Scanner inScn = new Scanner(inSm/*, "UTF-8"*/);//扫描器
			Pattern parttern=Pattern.compile(
					"http://wufazhuce.com/one/vol\\.(\\d+)");
			//正则表达式定义格局
			//找到最新的url即可，即找到最新的vol编号即可
			Matcher matcher;
			String str="";
			int vol=0;

			//获取vol标号
			while (inScn.hasNextLine()) { 	
				str=inScn.nextLine();
				str=str.trim();
				matcher=parttern.matcher(str);

				if (matcher.find()){
					str = matcher.group(1);//获取最新vol号
					vol=Integer.parseInt(str);
					System.out.println(vol);
					break;
				}
			}  


			while (inScn.hasNextLine()) { 	
				str=inScn.nextLine();
				str=str.trim();

				//date-day
				matcher=domPat.matcher(str);
				if (matcher.find()){
					str = deletHtml(str);
					System.out.print(str+" ");
				}

				//date-month year
				matcher=mayPat.matcher(str);
				if (matcher.find()){
					str = deletHtml(str);
					System.out.println(str);
					break;
				}
			}  

			return vol;

		} catch (IllegalStateException e) {
			// TODO 自动生成的 catch 块
			e.printStackTrace();
		} catch (IOException e) {
			// TODO 自动生成的 catch 块
			e.printStackTrace();
		}

		return 0;
	}


	private String deletHtml(String str) {
		Matcher matcher;

		matcher=htmlPattern.matcher(str);
		str=matcher.replaceAll("");
		return str;
	}


	public void visitTheOne(int volnumber) throws ClientProtocolException, IOException {
		int vol=0;
		hc=new DefaultHttpClient();

		try{
			httpget=new HttpGet("http://wufazhuce.com/");
			response=hc.execute(httpget);
			entity=response.getEntity();

			if (debug) {
				printConnect();		
			}

			vol=getNewestVol(entity);
			System.out.println(vol);

			//we must abort it after using or before other new created
			httpget.abort();
		}finally{

		}

		//visitVol(vol);
		visitVolsFromTo(vol-volnumber+1,vol);
		hc.getConnectionManager().shutdown();
	}

	/**
	 * 获取One中的cita，即每日一个
	 * @param entity
	 * @throws IllegalStateException
	 * @throws IOException
	 */
	protected void getCita(HttpEntity entity) throws IllegalStateException, IOException {
		InputStream inSm;

		inSm = entity.getContent();
		Scanner inScn = new Scanner(inSm/*, "UTF-8"*/);//扫描器
		Matcher matcher;
		
		String cita="";
		String data="";
		

	/*	
		<div class="one-pubdate">
        <p class="dom">12</p>
        <p class="may">Aug 2014</p>
    </div>
    */
		//获取vol标号
		while (inScn.hasNextLine()) {
			//检索http下一条
			String tmp=inScn.nextLine();
			tmp=tmp.trim();

			//定位指定条目
			matcher=prePattern.matcher(tmp);
			if (matcher.find()){
				tmp=inScn.nextLine();//取指定条目后一条
				tmp=deletHtml(tmp);//去除html元素
				tmp=tmp.trim();//去除空白符
				//System.out.println(tmp);
				cita=tmp;
				break;
			}
		}
		
		while (inScn.hasNextLine()) {
			//检索http下一条
			String tmp=inScn.nextLine();
			tmp=tmp.trim();
			
			matcher=domPat.matcher(tmp);
			if (matcher.find()) {		
				tmp=deletHtml(tmp);//去除html元素
				tmp=tmp.trim();//去除空白符
				//System.out.print(tmp);
				data=tmp+" ";
			}
			
			matcher=mayPat.matcher(tmp);
			if (matcher.find()) {
				tmp=deletHtml(tmp);//去除html元素
				tmp=tmp.trim();//去除空白符
				//System.out.print(tmp);
				data+=tmp;
				break;
			}
		}
		
		String msg=data+":"+cita;
		//msg=new String(msg.getBytes("gbk"));
		//msg=new String(msg.getBytes("GBK"));
		System.out.println(msg);
	}

	private void printConnect() {
		System.out.println("----------------------------------------");  
		System.out.println(response.getStatusLine());  
		if (entity != null) {  
			System.out.println("Response content length: " + entity.getContentLength());  
		}  
		System.out.println("----------------------------------------");  

	}


	public final static void main(String[] args) throws Exception {
		int volnumber=VOL_COUNT;
		
		try {
			if(args.length>=1){
				volnumber=new Integer(args[0]);
				System.out.println(""+volnumber);
			}
		} catch (Exception e) {
			// TODO: handle exception
		}
		
		CrawlerTheOne tc=new CrawlerTheOne();
		tc.visitTheOne(volnumber);
	}

}
